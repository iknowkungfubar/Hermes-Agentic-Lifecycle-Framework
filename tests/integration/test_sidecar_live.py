"""Integration tests requiring running sidecar server on port 9721."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request

import pytest

SIDECAR_URL = "http://127.0.0.1:9721"


def _sidecar_running() -> bool:
    """Check if sidecar is running."""
    try:
        r = urllib.request.urlopen(f"{SIDECAR_URL}/api/status", timeout=2)
        return r.status == 200
    except (urllib.error.URLError, ConnectionError):
        return False


@pytest.mark.skipif(not _sidecar_running(), reason="sidecar not running on :9721")
class TestHalfSidecarHTTP:
    """Tests against the live HTTP sidecar server."""

    def test_status_endpoint(self):
        r = urllib.request.urlopen(f"{SIDECAR_URL}/api/status", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert "status" in data

    def test_finality_endpoint(self):
        r = urllib.request.urlopen(
            f"{SIDECAR_URL}/api/get_finality_gate_status", timeout=5
        )
        assert r.status == 200
        data = json.loads(r.read())
        assert "locked" in data or "mrp_ready" in data

    def test_vram_endpoint(self):
        r = urllib.request.urlopen(f"{SIDECAR_URL}/api/vram", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert isinstance(data, dict)

    def test_stalled_endpoint(self):
        r = urllib.request.urlopen(f"{SIDECAR_URL}/api/stalled", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert isinstance(data, dict)
        assert "stalled" in data

    def test_diff_endpoint(self):
        r = urllib.request.urlopen(f"{SIDECAR_URL}/api/diff", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert isinstance(data, dict)


class TestHalfSidecarSubprocess:
    """Tests half_sidecar commands via subprocess."""

    @classmethod
    def setup_class(cls):
        import sys

        cls.python = sys.executable

    def test_cli_status(self):
        import os

        env = {**os.environ, "PYTHONPATH": "."}
        result = subprocess.run(
            [self.python, "-m", "half.half_sidecar", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cli_mrp(self):
        import os

        env = {**os.environ, "PYTHONPATH": "."}
        result = subprocess.run(
            [self.python, "-m", "half.half_sidecar", "mrp"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
