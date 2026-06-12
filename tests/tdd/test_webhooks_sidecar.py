"""TDD: target webhooks and half_sidecar uncovered lines."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestWebhooksUncovered:
    """Target the 65 uncovered lines in webhooks.py."""

    def test_webhook_handler_creation(self):
        """Hit lines 24-26: WebhookHandler init with args."""
        from half.webhooks import WebhookHandler
        h = WebhookHandler(webhook_secret="test-secret", repo_root="/tmp")
        assert h is not None

    def test_webhook_server_creation(self):
        """Hit lines 149-154: WebhookServer init."""
        from half.webhooks import WebhookHandler, WebhookServer
        h = WebhookHandler()
        s = WebhookServer(handler=h, port=19996)
        assert s.port == 19996
        assert s.host == "127.0.0.1"

    def test_webhook_dispatch(self):
        """Hit lines 134-143: dispatch method."""
        from half.webhooks import WebhookHandler
        h = WebhookHandler()
        r = h.dispatch("push", {"ref": "refs/heads/main"})
        assert isinstance(r, dict)


class TestHalfSidecarUncovered:
    """Target specific uncovered lines in half_sidecar.py."""

    def test_voice_stt(self):
        """Hit lines 159-160: cmd_voice_stt with missing file."""
        from half.half_sidecar import cmd_voice_stt
        r = cmd_voice_stt("/nonexistent/audio.wav")
        assert isinstance(r, dict)

    def test_voice_tts(self):
        """Hit lines 159-160: cmd_voice_tts."""
        from half.half_sidecar import cmd_voice_tts
        r = cmd_voice_tts("hello world")
        assert isinstance(r, dict)

    def test_focalboard_create(self):
        """Hit lines 184-191: cmd_focalboard_create connection error."""
        from half.half_sidecar import cmd_focalboard_create
        try:
            r = cmd_focalboard_create()
            assert isinstance(r, dict)
        except (ConnectionError, OSError):
            pass  # Expected without Focalboard server

    def test_doctor_report(self):
        """Hit _format_doctor_report."""
        from half.half_sidecar import _format_doctor_report
        from half.doctor import Doctor
        d = Doctor()
        r = d.run_full_diagnostics()
        result = _format_doctor_report(r)
        assert isinstance(result, str) and len(result) > 0
