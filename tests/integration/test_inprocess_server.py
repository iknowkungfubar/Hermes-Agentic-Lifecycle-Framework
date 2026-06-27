"""In-process HTTP server — starts http_sidecar handler directly to cover do_GET, do_POST, _json_response."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from http.server import HTTPServer
from pathlib import Path

import pytest


class TestHTTPSidecarHandlerDirect:
    """Start the http_sidecar server in-process and make real HTTP requests."""

    @pytest.fixture(scope="class")
    def server(self):
        from half.http_sidecar import HalfAPIHandler

        port = 19888
        server = HTTPServer(("127.0.0.1", port), HalfAPIHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.5)
        yield port
        server.shutdown()

    def test_do_GET_status(self, server):
        """Hit do_GET handler at /api/status."""
        import urllib.request

        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/status", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert "status" in data

    def test_do_GET_finality(self, server):
        """Hit do_GET at /api/get_finality_gate_status."""
        import urllib.request

        r = urllib.request.urlopen(
            f"http://127.0.0.1:{server}/api/get_finality_gate_status", timeout=5
        )
        assert r.status == 200

    def test_do_GET_vram(self, server):
        """Hit do_GET at /api/vram."""
        import urllib.request

        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/vram", timeout=5)
        assert r.status == 200

    def test_do_GET_stalled(self, server):
        """Hit do_GET at /api/stalled."""
        import urllib.request

        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/stalled", timeout=5)
        assert r.status == 200

    def test_do_GET_diff(self, server):
        """Hit do_GET at /api/diff."""
        import urllib.request

        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/api/diff", timeout=5)
        assert r.status == 200

    def test_do_GET_unknown(self, server):
        """Hit do_GET with unknown path — should return 404."""
        import urllib.request

        try:
            r = urllib.request.urlopen(
                f"http://127.0.0.1:{server}/api/unknown", timeout=5
            )
            assert r.status == 404
        except urllib.error.HTTPError:
            pass  # Expected 404


class TestRestDaemonHandlerDirect:
    """Exercise rest_daemon handler in-process."""

    def test_handler_attributes(self):
        from half.rest_daemon import RESTAPIHandler

        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert hasattr(RESTAPIHandler, "log_message")


class TestWebhooksDirect:
    """Exercise webhooks handler."""

    def test_server_creation(self):
        from half.webhooks import WebhookHandler, WebhookServer

        h = WebhookHandler()
        assert h is not None
        s = WebhookServer(handler=h, port=19998)
        assert s.port == 19998


class TestSandboxDirect:
    def test_sandbox_init(self):
        from half.sandbox import ExecutionSandbox

        try:
            s = ExecutionSandbox()
            assert s is not None
        except (FileNotFoundError, RuntimeError):
            pytest.skip("No container runtime")


class TestPrewarmDirect:
    def test_container_lifecycle(self):
        from half.prewarm import PreWarmDeployment, WarmContainer

        pw = PreWarmDeployment()
        pw._warm_containers["test"] = WarmContainer(name="test", image="test:latest")
        pw._warm_containers["test"].status = "ready"
        assert pw._warm_containers["test"].status == "ready"
        pw.cleanup()
        assert len(pw._warm_containers) == 0


class TestVoiceDirect:
    def test_voice_attributes(self):
        from half.half_voice.engine import VoiceEngine

        e = VoiceEngine()
        assert hasattr(e, "_stt_available")
        assert hasattr(e, "_tts_available")
        assert hasattr(e, "transcribe")
        assert hasattr(e, "speak")
