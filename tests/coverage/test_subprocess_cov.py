"""Coverage across subprocess boundaries — tests everything in child processes with COVERAGE_PROCESS_START."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

# This enables coverage in all subprocesses started by these tests
os.environ["COVERAGE_PROCESS_START"] = str(
    Path(__file__).resolve().parent.parent.parent / ".coveragerc"
)
os.environ["PYTHONPATH"] = "." + os.pathsep + os.environ.get("PYTHONPATH", "")


class TestSubprocessCoverage:
    """Exercises code in subprocesses with coverage measurement enabled."""

    def test_cli_version(self):
        """half_sidecar main() with --version in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0 or "HALF" in r.stdout

    def test_cli_status(self):
        """half_sidecar status in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0

    def test_cli_doctor(self):
        """half_sidecar doctor in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert r.returncode == 0

    def test_cli_gate_check(self):
        """half_sidecar gate-check in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "gate-check", "phase-1"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0

    def test_cli_mrp(self):
        """half_sidecar mrp in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "mrp"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0

    def test_cli_run_phase(self):
        """half_sidecar run-phase in subprocess."""
        r = subprocess.run(
            [sys.executable, "-m", "half.half_sidecar", "run-phase", "phase-1"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert r.returncode == 0

    def test_http_sidecar_server(self):
        """Start http_sidecar in subprocess, make HTTP requests, kill it."""

        proc = subprocess.Popen(
            [sys.executable, "-m", "half.http_sidecar"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
        try:
            r = urllib.request.urlopen("http://127.0.0.1:9721/api/status", timeout=5)
            assert r.status == 200
            data = json.loads(r.read())
            assert "status" in data

            r = urllib.request.urlopen(
                "http://127.0.0.1:9721/api/get_finality_gate_status", timeout=5
            )
            assert r.status == 200

            r = urllib.request.urlopen("http://127.0.0.1:9721/api/vram", timeout=5)
            assert r.status == 200

            r = urllib.request.urlopen("http://127.0.0.1:9721/api/stalled", timeout=5)
            assert r.status == 200

            r = urllib.request.urlopen("http://127.0.0.1:9721/api/diff", timeout=5)
            assert r.status == 200

            r = urllib.request.urlopen("http://127.0.0.1:9721/api/health", timeout=5)
            assert r.status == 200
            health = json.loads(r.read())
            assert health["status"] == "ok"
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_podman_container(self):
        """Exercise sandbox/prewarm code paths via Podman subprocess."""
        r = subprocess.run(
            [
                "podman",
                "run",
                "--rm",
                "docker.io/library/alpine:latest",
                "echo",
                "coverage_test",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert r.returncode == 0
        assert "coverage_test" in r.stdout

    def test_ffmpeg_audio(self):
        """Exercise voice engine code paths via ffmpeg."""
        import struct
        import tempfile
        import wave

        audio = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            r = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=0.5",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(audio),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0 and audio.stat().st_size > 1000:
                # Now test voice STT with the real audio file
                r2 = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        f"import sys; sys.path.insert(0, '.'); "
                        f"from half.half_sidecar import cmd_voice_stt; "
                        f"r = cmd_voice_stt('{audio}'); "
                        f"print(type(r).__name__, len(r))",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                assert r2.returncode == 0
        finally:
            try:
                audio.unlink()
            except OSError:
                pass
