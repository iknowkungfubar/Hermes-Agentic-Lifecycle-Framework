"""Integration tests with real HTTP server on port 9721."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SIDECAR_URL = "http://127.0.0.1:9721"


@pytest.fixture(scope="module")
def sidecar_server():
    """Kill any existing sidecar, start fresh, yield, then clean up."""
    # Kill existing
    subprocess.run(["pkill", "-f", "half.http_sidecar"], capture_output=True, timeout=5)
    time.sleep(1)

    env = {**os.environ, "PYTHONPATH": "."}
    proc = subprocess.Popen(
        [sys.executable, "-m", "half.http_sidecar"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server
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


class TestLiveHTTP:
    """All tests against the live HTTP sidecar."""

    def test_status(self, sidecar_server):
        r = urllib.request.urlopen(f"{sidecar_server}/api/status", timeout=5)
        assert r.status == 200
        assert "status" in json.loads(r.read())

    def test_finality(self, sidecar_server):
        r = urllib.request.urlopen(
            f"{sidecar_server}/api/get_finality_gate_status", timeout=5
        )
        assert r.status == 200

    def test_vram(self, sidecar_server):
        r = urllib.request.urlopen(f"{sidecar_server}/api/vram", timeout=5)
        assert r.status == 200

    def test_stalled(self, sidecar_server):
        r = urllib.request.urlopen(f"{sidecar_server}/api/stalled", timeout=5)
        assert r.status == 200

    def test_diff(self, sidecar_server):
        r = urllib.request.urlopen(f"{sidecar_server}/api/diff", timeout=5)
        assert r.status == 200
