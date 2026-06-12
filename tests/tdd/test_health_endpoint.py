"""TDD: /api/health endpoint — must fail first, then implement."""

from __future__ import annotations

import json
from http.server import HTTPServer
import threading
import time
import urllib.request

import pytest


class TestHealthEndpoint:
    """RED phase: test must fail because /api/health doesn't exist yet."""

    @pytest.fixture(scope="class")
    def server(self):
        from half.http_sidecar import HalfAPIHandler
        port = 19777
        srv = HTTPServer(("127.0.0.1", port), HalfAPIHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)
        yield port
        srv.shutdown()

    def test_health_returns_200(self, server):
        """/api/health should respond with 200."""
        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/health", timeout=5)
        assert r.status == 200

    def test_health_has_status_ok(self, server):
        """Response body should contain status: ok."""
        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/health", timeout=5)
        data = json.loads(r.read())
        assert data["status"] == "ok"

    def test_health_has_version(self, server):
        """Response body should contain version string."""
        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/health", timeout=5)
        data = json.loads(r.read())
        assert "version" in data
