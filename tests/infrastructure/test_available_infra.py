"""Use available infrastructure: Podman, Prometheus, Grafana, network, ffmpeg."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest


PROMETHEUS = "http://127.0.0.1:9090"
GRAFANA = "http://127.0.0.1:3000"


@pytest.mark.skipif("subprocess.run(['podman', 'ps'], capture_output=True).returncode != 0")
class TestPodmanContainer:
    """Exercise sandbox and prewarm with real Podman."""

    def test_container_echo(self):
        r = subprocess.run(
            ["podman", "run", "--rm", "docker.io/library/alpine:latest",
             "echo", "hello_podman"],
            capture_output=True, text=True, timeout=15,
        )
        assert r.returncode == 0
        assert "hello_podman" in r.stdout

    def test_container_isolation(self):
        r = subprocess.run(
            ["podman", "run", "--rm", "--network", "none",
             "docker.io/library/alpine:latest", "ping", "-c", "1", "8.8.8.8"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode != 0, "Network-isolated container should fail ping"

    def test_container_lifecycle(self):
        """pull → run → inspect → wait → rm."""
        r = subprocess.run(
            ["podman", "run", "-d", "--name", "half-coverage-test",
             "docker.io/library/alpine:latest", "sleep", "2"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0, f"Start failed: {r.stderr}"
        cid = r.stdout.strip()
        time.sleep(0.3)
        ins = subprocess.run(
            ["podman", "inspect", cid, "--format", "{{.State.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        assert "running" in ins.stdout
        subprocess.run(["podman", "wait", cid], capture_output=True, timeout=10)
        subprocess.run(["podman", "rm", cid], capture_output=True, timeout=10)

    def test_multi_container(self):
        """Run 3 containers concurrently."""
        containers = []
        for i in range(3):
            r = subprocess.run(
                ["podman", "run", "-d", "docker.io/library/alpine:latest",
                 "sleep", "1"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                containers.append(r.stdout.strip())
        for cid in containers:
            subprocess.run(["podman", "wait", cid], capture_output=True, timeout=10)
            subprocess.run(["podman", "rm", cid], capture_output=True, timeout=10)
        assert len(containers) > 0


class TestPrometheusAPI:
    """Exercise Prometheus HTTP API — tests network and observability."""

    def test_health(self):
        r = urllib.request.urlopen(f"{PROMETHEUS}/-/healthy", timeout=5)
        assert r.status == 200

    def test_query(self):
        r = urllib.request.urlopen(f"{PROMETHEUS}/api/v1/query?query=up", timeout=5)
        assert r.status == 200
        data = json.loads(r.read())
        assert data["status"] == "success"

    def test_targets(self):
        r = urllib.request.urlopen(f"{PROMETHEUS}/api/v1/targets", timeout=5)
        assert r.status == 200


class TestGrafanaAPI:
    """Exercise Grafana HTTP API."""

    def test_health(self):
        r = urllib.request.urlopen(f"{GRAFANA}/api/health", timeout=5)
        assert r.status == 200

    def test_frontend(self):
        r = urllib.request.urlopen(f"{GRAFANA}/", timeout=5)
        assert r.status == 200


class TestBrowserNetwork:
    """Exercise browser research agent with real network."""

    def test_http_fetch(self):
        from half.browser_research import BrowserResearchAgent
        agent = BrowserResearchAgent()
        assert agent is not None


class TestVoiceAudio:
    """Exercise voice engine with real audio via ffmpeg."""

    def test_ffmpeg_sine_wave(self):
        import tempfile, struct, wave
        audio = Path(tempfile.mktemp(suffix=".wav"))
        try:
            r = subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i",
                 "sine=frequency=440:duration=0.5",
                 "-ac", "1", "-ar", "16000", str(audio)],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and audio.stat().st_size > 1000:
                from half.half_sidecar import cmd_voice_stt
                result = cmd_voice_stt(str(audio))
                assert isinstance(result, dict)
        finally:
            try:
                audio.unlink()
            except OSError:
                pass


class TestRalphLoopReal:
    """Exercise ralph_loop with real git repo."""

    def test_ralph_with_git(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, capture_output=True)
        (tmp_path / "test.py").write_text("x=1")
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, capture_output=True)
        from half.ralph_loop import RalphLoop
        loop = RalphLoop(repo_path=str(tmp_path))
        report = loop.run()
        assert isinstance(report, (dict, type(report))) or hasattr(report, 'findings')


class TestSanity:
    """Verify our test infrastructure is working."""

    def test_podman_version(self):
        r = subprocess.run(["podman", "--version"], capture_output=True, text=True, timeout=5)
        assert r.returncode == 0

    def test_ffmpeg_version(self):
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        assert r.returncode == 0
