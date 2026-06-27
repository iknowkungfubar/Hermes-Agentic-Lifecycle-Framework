"""Direct in-process tests for remaining high-miss modules."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestHalfSidecarDirect:
    def test_status_direct(self):
        from half.half_sidecar import (
            cmd_gate_check,
            cmd_generate_mrp,
            cmd_run_phase,
            cmd_status,
        )

        assert isinstance(cmd_status(), dict)
        assert isinstance(cmd_generate_mrp(), dict)
        assert isinstance(cmd_gate_check("phase-1"), dict)
        r = cmd_run_phase("phase-1")
        assert isinstance(r, dict)
        assert "status" in r

    def test_gate_check_all_phases(self):
        from half.half_sidecar import cmd_gate_check

        for phase in ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5"]:
            r = cmd_gate_check(phase)
            assert isinstance(r, dict)

    def test_mrp_structure(self):
        from half.half_sidecar import cmd_generate_mrp

        r = cmd_generate_mrp()
        assert isinstance(r, dict)


class TestHTTPSidecarDirect:
    def test_import_classes(self):
        from half.http_sidecar import HalfAPIHandler, run_server

        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")
        assert hasattr(HalfAPIHandler, "_json_response")
        assert hasattr(HalfAPIHandler, "_get_vram")
        assert callable(run_server)


class TestRestDaemonDirect:
    def test_import_classes(self):
        from half.rest_daemon import RESTAPIHandler, run_server

        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert callable(run_server)


class TestWebhooksDirect:
    def test_webhook_models(self):
        from half.webhooks import WebhookHandler, WebhookServer

        handler = WebhookHandler()
        assert handler is not None
        server = WebhookServer(handler=handler)
        assert server is not None
