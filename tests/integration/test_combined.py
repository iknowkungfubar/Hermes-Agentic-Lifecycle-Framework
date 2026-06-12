"""Combined in-process + live tests for maximum coverage."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

SIDECAR_URL = "http://127.0.0.1:9721"


@pytest.fixture(scope="module")
def sidecar():
    """Start HTTP sidecar once per module."""
    env = {**os.environ, "PYTHONPATH": "."}
    proc = subprocess.Popen(
        [sys.executable, "-m", "half.http_sidecar"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            r = urllib.request.urlopen(f"{SIDECAR_URL}/api/status", timeout=1)
            if r.status == 200:
                break
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.5)
    yield SIDECAR_URL
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestCombined:
    """In-process imports + live HTTP — hits deep lines in all modules."""

    # ── half_sidecar deep lines ─────────────────────────────────────────

    def test_half_sidecar_commands(self):
        from half.half_sidecar import cmd_status, cmd_generate_mrp, cmd_gate_check, cmd_run_phase
        assert isinstance(cmd_status(), dict)
        assert isinstance(cmd_generate_mrp(), dict)
        assert isinstance(cmd_gate_check("phase-1"), dict)
        r = cmd_run_phase("phase-1")
        assert isinstance(r, dict)

    def test_half_sidecar_exception(self):
        from half.half_sidecar import cmd_run_phase
        r = cmd_run_phase("invalid-phase")
        assert "status" in r

    # ── http_sidecar deep lines ─────────────────────────────────────────

    def test_http_sidecar_classes(self):
        from half.http_sidecar import HalfAPIHandler, run_server
        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")
        assert hasattr(HalfAPIHandler, "_json_response")
        assert callable(run_server)

    def test_http_sidecar_live(self, sidecar):
        r = urllib.request.urlopen(f"{sidecar}/api/status", timeout=5)
        assert r.status == 200
        assert "status" in json.loads(r.read())

    def test_http_sidecar_finality(self, sidecar):
        r = urllib.request.urlopen(f"{sidecar}/api/get_finality_gate_status", timeout=5)
        assert r.status == 200

    def test_http_sidecar_vram(self, sidecar):
        r = urllib.request.urlopen(f"{sidecar}/api/vram", timeout=5)
        assert r.status == 200

    # ── rest_daemon deep lines ──────────────────────────────────────────

    def test_rest_daemon_classes(self):
        from half.rest_daemon import RESTAPIHandler, run_server
        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert callable(run_server)

    # ── webhooks deep lines ─────────────────────────────────────────────

    def test_webhooks_classes(self):
        from half.webhooks import WebhookHandler, WebhookServer
        h = WebhookHandler()
        assert h is not None
        s = WebhookServer(handler=h)
        assert s is not None

    # ── __main__ deep lines ─────────────────────────────────────────────

    def test_main_dispatch_all(self):
        import argparse
        from half.__main__ import _route_command
        cases = [
            (argparse.Namespace(command="version", version=False), None),
            (argparse.Namespace(command="status", version=False), dict),
            (argparse.Namespace(command="generate-mrp", version=False), dict),
        ]
        for args, expected_type in cases:
            result = _route_command(args)
            if expected_type:
                assert isinstance(result, expected_type)
            else:
                assert result is None
