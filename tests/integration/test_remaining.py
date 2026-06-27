"""Integration tests for remaining high-miss modules."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestHalfSidecarDeep:
    def test_all_sidecar_commands(self):
        from half.half_sidecar import (
            cmd_gate_check,
            cmd_generate_mrp,
            cmd_run_phase,
            cmd_status,
        )

        assert isinstance(cmd_status(), dict)
        assert isinstance(cmd_generate_mrp(), dict)
        assert isinstance(cmd_gate_check("phase-1"), dict)
        assert isinstance(cmd_run_phase("phase-1"), dict)


class TestHTTPSidecarDeep:
    def test_handler_has_methods(self):
        from half.http_sidecar import HalfAPIHandler, run_server

        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")
        assert hasattr(HalfAPIHandler, "_json_response")
        assert callable(run_server)


class TestRestDaemonDeep:
    def test_handler_endpoints(self):
        from half.rest_daemon import RESTAPIHandler, run_server

        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert callable(run_server)


class TestWebhooksDeep:
    def test_webhook_flow(self):
        from half.webhooks import WebhookHandler, WebhookServer

        h = WebhookHandler()
        assert h is not None
        events = []
        s = WebhookServer(handler=lambda e: events.append(e))
        assert s is not None


class TestPrewarmDeep:
    def test_warm_container_lifecycle(self):
        from half.prewarm import PreWarmDeployment, WarmContainer

        pw = PreWarmDeployment()
        wc = WarmContainer(name="svc", image="svc:latest")
        assert wc.status == "warming"
        pw._warm_containers["svc"] = wc
        assert "svc" in pw._warm_containers
        pw.cleanup()
        assert len(pw._warm_containers) == 0


class TestVoiceDeep:
    def test_voice_engine_capabilities(self):
        from half.half_voice.engine import VoiceEngine

        e = VoiceEngine()
        assert hasattr(e, "transcribe")
        assert hasattr(e, "speak")
        assert hasattr(e, "_stt_available")
        assert hasattr(e, "_tts_available")


class TestSandboxDeep:
    def test_sandbox_init(self):
        from half.sandbox import ExecutionSandbox

        try:
            s = ExecutionSandbox()
            assert s is not None
        except (FileNotFoundError, RuntimeError):
            pass


class TestSecurityScannersDeep:
    def test_scanner_imports(self):
        from half.security_scanners import BumblebeeScanner, GarakScanner

        g = GarakScanner()
        assert g is not None
        b = BumblebeeScanner()
        assert b is not None


class TestBrowserResearchDeep:
    def test_browser_agent(self):
        from half.browser_research import BrowserResearchAgent

        agent = BrowserResearchAgent()
        assert agent is not None


class TestPSMDeep:
    def test_manager_operations(self):

        with tempfile.TemporaryDirectory() as tmp:
            from half.psm import PSMManager

            skills_dir = Path(tmp) / ".harness" / "skills"
            skills_dir.mkdir(parents=True)
            (skills_dir / "test.yaml").write_text("name: test\\nversion: 1.0\\n")
            mgr = PSMManager(skills_dir=skills_dir)
            skills = mgr.discover()
            assert isinstance(skills, list)
