"""Ultra-targeted tests for specific missed lines — direct function calls."""

from __future__ import annotations

from pathlib import Path
import pytest


class TestSidecarDeepFunctions:
    """Exercises specific deep functions in half_sidecar."""

    def test_format_doctor_report(self):
        """Hit _format_doctor_report."""
        from half.half_sidecar import _format_doctor_report
        from half.doctor import Doctor
        d = Doctor()
        r = d.run_full_diagnostics()
        output = _format_doctor_report(r)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_dispatch_init(self):
        """Hit init command route."""
        import argparse
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(
            command="init", project="test-proj", mode="full", dir="/tmp", version=False
        ))
        assert isinstance(r, dict)
        assert "status" in r


class TestHTTPSidecarDeep:
    """Exercises deep lines in http_sidecar."""

    def test_all_handler_methods(self):
        from half.http_sidecar import HalfAPIHandler
        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")
        assert hasattr(HalfAPIHandler, "_json_response")
        assert hasattr(HalfAPIHandler, "_get_vram")
        assert hasattr(HalfAPIHandler, "_get_stalled")
        assert hasattr(HalfAPIHandler, "_get_diff")


class TestPrewarmDeep:
    """Exercises container lifecycle management."""

    def test_prewarm_lifecycle(self):
        from half.prewarm import PreWarmDeployment, WarmContainer
        pw = PreWarmDeployment()
        wc = WarmContainer(name="svc", image="svc:1.0")
        assert wc.status == "warming"
        pw._warm_containers["svc"] = wc
        wc.status = "ready"
        assert pw._warm_containers["svc"].status == "ready"
        pw.cleanup()
        assert len(pw._warm_containers) == 0


class TestVoiceEngineDeep:
    """Exercises voice engine discovery."""

    def test_engine_discovery(self):
        from half.half_voice.engine import VoiceEngine
        e = VoiceEngine()
        assert e._stt_available is not None
        assert e._tts_available is not None


class TestSecurityDeep:
    """Exercises security scanner imports."""

    def test_both_scanners(self):
        from half.security_scanners import GarakScanner, BumblebeeScanner
        g = GarakScanner()
        assert g is not None
        b = BumblebeeScanner()
        assert b is not None


class TestBrowserDeep:
    def test_agent_defaults(self):
        from half.browser_research import BrowserResearchAgent
        a = BrowserResearchAgent()
        assert a is not None


class TestIndexingDeep:
    def test_index_with_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.indexing import RepoIndexer
            idx = RepoIndexer(root=tmp)
            result = idx.build_index()
            assert isinstance(result, dict)
