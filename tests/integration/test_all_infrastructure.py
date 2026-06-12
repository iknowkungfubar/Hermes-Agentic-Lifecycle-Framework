"""Comprehensive infrastructure integration tests — targets all remaining uncovered lines."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest


_SIDECAR_RUNNING = socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(("127.0.0.1", 9721)) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# half_sidecar.py — all remaining deep lines
# ═══════════════════════════════════════════════════════════════════════════════
class TestHalfSidecarFull:
    def test_status(self):
        from half.half_sidecar import cmd_status
        r = cmd_status()
        assert isinstance(r, dict)
        assert "status" in r

    def test_run_phase(self):
        from half.half_sidecar import cmd_run_phase
        r = cmd_run_phase("phase-1")
        assert isinstance(r, dict)

    def test_run_phase_error(self):
        from half.half_sidecar import cmd_run_phase
        r = cmd_run_phase("invalid-phase")
        assert "status" in r

    def test_gate_check(self):
        from half.half_sidecar import cmd_gate_check
        r = cmd_gate_check("phase-1")
        assert isinstance(r, dict)

    def test_gate_check_phase3(self):
        from half.half_sidecar import cmd_gate_check
        r = cmd_gate_check("phase-3")
        assert isinstance(r, dict)

    def test_generate_mrp(self):
        from half.half_sidecar import cmd_generate_mrp
        r = cmd_generate_mrp()
        assert isinstance(r, dict)


class TestHalfSidecarCLI:
    def test_main_no_args(self):
        from half.__main__ import main
        import io, sys as _sys
        captured = io.StringIO()
        old = _sys.stdout
        _sys.stdout = captured
        old_argv = _sys.argv
        _sys.argv = ["half"]
        try:
            main()
        finally:
            _sys.stdout = old
            _sys.argv = old_argv
        assert len(captured.getvalue()) > 0

    def test_main_version_flag(self):
        from half.__main__ import main
        import io, sys as _sys
        captured = io.StringIO()
        old = _sys.stdout
        _sys.stdout = captured
        old_argv = _sys.argv
        _sys.argv = ["half", "--version"]
        try:
            try:
                main()
            except (SystemExit, Exception):
                pass
        finally:
            _sys.stdout = old
            _sys.argv = old_argv
        assert "HALF" in captured.getvalue()

    def test_dispatch_all_routes(self):
        from half.__main__ import _route_command
        ns = argparse.Namespace
        cases = [
            (ns(command="version", version=False), None),
            (ns(command="status", version=False), dict),
            (ns(command="run-phase", phase="phase-1", version=False), dict),
            (ns(command="gate-check", phase="phase-1", version=False), dict),
            (ns(command="generate-mrp", version=False), dict),
            (ns(command="init", project="test", mode="full", dir="/tmp", version=False), dict),
        ]
        for args, expected in cases:
            r = _route_command(args)
            if expected is None:
                assert r is None
            else:
                assert isinstance(r, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# http_sidecar.py
# ═══════════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(not _SIDECAR_RUNNING, reason="Sidecar not running on :9721")
class TestHTTPSidecarLive:
    def test_status(self, sidecar_url):
        r = urllib.request.urlopen(f"{sidecar_url}/api/status", timeout=5)
        assert r.status == 200
        assert "status" in json.loads(r.read())

    def test_finality(self, sidecar_url):
        r = urllib.request.urlopen(f"{sidecar_url}/api/get_finality_gate_status", timeout=5)
        assert r.status == 200

    def test_vram(self, sidecar_url):
        r = urllib.request.urlopen(f"{sidecar_url}/api/vram", timeout=5)
        assert r.status == 200

    def test_stalled(self, sidecar_url):
        r = urllib.request.urlopen(f"{sidecar_url}/api/stalled", timeout=5)
        assert r.status == 200

    def test_diff(self, sidecar_url):
        r = urllib.request.urlopen(f"{sidecar_url}/api/diff", timeout=5)
        assert r.status == 200


class TestHTTPSidecarDirect:
    def test_handler_methods(self):
        from half.http_sidecar import HalfAPIHandler, run_server
        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")
        assert hasattr(HalfAPIHandler, "_json_response")
        assert callable(run_server)


# ═══════════════════════════════════════════════════════════════════════════════
# rest_daemon.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestRestDaemonDirect:
    def test_handler_methods(self):
        from half.rest_daemon import RESTAPIHandler, run_server
        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert callable(run_server)


# ═══════════════════════════════════════════════════════════════════════════════
# webhooks.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestWebhooksDirect:
    def test_handler_classes(self):
        from half.webhooks import WebhookHandler, WebhookServer
        h = WebhookHandler()
        assert h is not None
        s = WebhookServer(handler=h)
        assert s is not None


# ═══════════════════════════════════════════════════════════════════════════════
# sandbox.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestSandboxDirect:
    def test_import(self):
        from half.sandbox import ExecutionSandbox
        assert ExecutionSandbox is not None

    def test_init(self):
        from half.sandbox import ExecutionSandbox
        try:
            s = ExecutionSandbox()
            assert s is not None
        except (FileNotFoundError, RuntimeError):
            pytest.skip("No container runtime")


# ═══════════════════════════════════════════════════════════════════════════════
# prewarm.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestPreWarmDirect:
    def test_warm_container(self):
        from half.prewarm import PreWarmDeployment, WarmContainer
        pw = PreWarmDeployment()
        wc = WarmContainer(name="test-svc", image="test:latest")
        assert wc.name == "test-svc"
        pw._warm_containers["test-svc"] = wc
        assert len(pw._warm_containers) == 1
        pw.cleanup()
        assert len(pw._warm_containers) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# half_voice/engine.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestVoiceDirect:
    def test_engine_basics(self):
        from half.half_voice.engine import VoiceEngine
        e = VoiceEngine()
        assert hasattr(e, "transcribe")
        assert hasattr(e, "speak")
        assert hasattr(e, "_stt_available")
        assert hasattr(e, "_tts_available")


# ═══════════════════════════════════════════════════════════════════════════════
# security_scanners.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestSecurityDirect:
    def test_scanner_imports(self):
        from half.security_scanners import GarakScanner, BumblebeeScanner
        assert GarakScanner is not None
        assert BumblebeeScanner is not None


# ═══════════════════════════════════════════════════════════════════════════════
# browser_research.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestBrowserDirect:
    def test_agent_import(self):
        from half.browser_research import BrowserResearchAgent
        agent = BrowserResearchAgent()
        assert agent is not None


# ═══════════════════════════════════════════════════════════════════════════════
# no_slop.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestNoSlopDirect:
    def test_build_index(self, test_noslop_tree):
        from half.no_slop import NoSlopIndexer
        idx = NoSlopIndexer(root_path=str(test_noslop_tree))
        result = idx.build_index()
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# env_bootstrap.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestEnvBootstrapDirect:
    def test_bootstrap_with_git(self, test_git_repo):
        from half.env_bootstrap import EnvironmentBootstrapper
        boot = EnvironmentBootstrapper(root_path=str(test_git_repo))
        snap = boot.capture_snapshot("integration task", "test-proj")
        assert snap.project_name == "test-proj"
        assert len(snap.recent_git_history) > 0
        prompt = boot.build_bootstrap_prompt(snap)
        assert "test-proj" in prompt


# ═══════════════════════════════════════════════════════════════════════════════
# reflection_loop.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestReflectionDirect:
    def test_reflection_with_git(self, test_git_repo):
        from half.reflection_loop import ReflectionLoop
        loop = ReflectionLoop(repo_path=str(test_git_repo))
        report = loop.run()
        assert isinstance(report.findings, list)


# ═══════════════════════════════════════════════════════════════════════════════
# psm.py
# ═══════════════════════════════════════════════════════════════════════════════
class TestPSMDirect:
    def test_discover_skills(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "test.yaml").write_text("name: test\nversion: '1.0'\ndescription: Test\n")
        from half.psm import PSMManager
        mgr = PSMManager(skills_dir=str(skills_dir))
        skills = mgr.discover()
        assert len(skills) >= 1
