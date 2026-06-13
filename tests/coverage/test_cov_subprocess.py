"""Coverage in subprocesses using temp files + coverage run."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent.parent


def cov_run_module(module_name: str, args: list[str] | None = None, **kw):
    """Run a Python module with coverage measurement."""
    cmd = [sys.executable, "-m", "coverage", "run",
           "--source=src/half", "--parallel-mode",
           "-m", module_name] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=HERE, **kw)


def cov_run_code(code: str, **kw):
    """Run inline Python code with coverage via a temp file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmpfile = f.name
    try:
        cmd = [sys.executable, "-m", "coverage", "run",
               "--source=src/half", "--parallel-mode",
               tmpfile]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=HERE, **kw)
        return result
    finally:
        Path(tmpfile).unlink(missing_ok=True)


class TestCLICoverage:
    """CLI commands under coverage."""

    def test_version(self):
        r = cov_run_module("half.half_sidecar", ["--version"])
        assert r.returncode == 0, f"stderr: {r.stderr[:100]}"

    def test_status(self):
        r = cov_run_module("half.half_sidecar", ["status"])
        assert r.returncode == 0

    def test_doctor(self):
        r = cov_run_module("half.half_sidecar", ["doctor"])
        assert r.returncode == 0

    def test_gate_check(self):
        r = cov_run_module("half.half_sidecar", ["gate-check", "phase-1"])
        assert r.returncode == 0

    def test_mrp(self):
        r = cov_run_module("half.half_sidecar", ["mrp"])
        assert r.returncode == 0


class TestHTTPSidecarCoverage:
    """HTTP sidecar under coverage."""
    def test_all_endpoints(self):
        """Start server with coverage, hit all endpoints."""
        import os
        os.system("pkill -f 'half.http_sidecar' 2>/dev/null")
        time.sleep(1)
        proc = subprocess.Popen(
            [sys.executable, "-m", "coverage", "run",
             "--source=src/half", "--parallel-mode",
             "-m", "half.http_sidecar"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        try:
            import urllib.request
            for ep in ["/api/status", "/api/get_finality_gate_status",
                       "/api/vram", "/api/stalled", "/api/diff", "/api/health"]:
                r = urllib.request.urlopen(f"http://127.0.0.1:9721{ep}", timeout=5)
                assert r.status == 200
        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestInProcessCoverage:
    """Deep code paths under coverage."""

    def test_webhooks(self):
        r = cov_run_code("""
from half.webhooks import WebhookHandler
h = WebhookHandler(webhook_secret="s", repo_root="/tmp")
for ev, pl in [
    ("push", {"ref": "main", "commits": [{"id": "a"}]}),
    ("issues", {"action": "opened", "issue": {"number": 1}}),
    ("pull_request", {"action": "opened", "pull_request": {"number": 1}}),
    ("ping", {}),
]:
    assert isinstance(h.dispatch(ev, pl), dict)
print("OK")
""")
        assert r.returncode == 0, f"stderr: {r.stderr[:200]}"
        assert "OK" in r.stdout

    def test_sandbox(self):
        r = cov_run_code("from half.sandbox import ExecutionSandbox; print('OK')")
        assert r.returncode == 0

    def test_prewarm(self):
        r = cov_run_code("""
from half.prewarm import PreWarmDeployment, WarmContainer
pw = PreWarmDeployment()
pw._warm_containers["a"] = WarmContainer(name="a", image="a:latest")
pw._warm_containers["b"] = WarmContainer(name="b", image="b:latest")
assert len(pw._warm_containers) == 2
pw.cleanup()
assert len(pw._warm_containers) == 0
print("OK")
""")
        assert r.returncode == 0

    def test_voice(self):
        r = cov_run_code("from half.half_voice.engine import VoiceEngine; e = VoiceEngine(); print('OK')")
        assert r.returncode == 0

    def test_security(self):
        r = cov_run_code("from half.security_scanners import GarakScanner, BumblebeeScanner; print('OK')")
        assert r.returncode == 0

    def test_browser(self):
        r = cov_run_code("from half.browser_research import BrowserResearchAgent; a = BrowserResearchAgent(); print('OK')")
        assert r.returncode == 0

    def test_rest_daemon(self):
        r = cov_run_code("from half.rest_daemon import RESTAPIHandler, run_server; print('OK')")
        assert r.returncode == 0

    def test_stale_monitor(self):
        r = cov_run_code("from half.stale_monitor import StaleSessionMonitor; m = StaleSessionMonitor(); m.scan(); print('OK')")
        assert r.returncode == 0

    def test_ralph_loop(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.name", "T"], cwd=tmp, capture_output=True)
            (Path(tmp) / "f.py").write_text("x=1")
            (Path(tmp) / ".harness").mkdir()
            (Path(tmp) / ".harness" / "agents.md").write_text("# Rules")
            subprocess.run(["git", "add", "-A"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp, capture_output=True)
            r = cov_run_code(f"""
import sys
sys.path.insert(0, '.')
from half.ralph_loop import RalphLoop
r = RalphLoop(repo_path=r'{tmp}').run()
assert isinstance(r.findings, list)
print("OK")
""")
            assert r.returncode == 0
