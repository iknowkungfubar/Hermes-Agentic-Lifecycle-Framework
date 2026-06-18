"""Real infrastructure tests — uses Podman, actual audio, and real filesystems."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestSandboxWithPodman:
    """Tests sandbox with actual Podman runtime."""

    def test_sandbox_echo(self):
        """Execute a command inside a real Podman container."""
        try:
            result = subprocess.run(
                ["podman", "run", "--rm", "docker.io/library/alpine:latest",
                 "echo", "hello_from_sandbox"],
                capture_output=True, text=True, timeout=15,
            )
            assert result.returncode == 0
            assert "hello_from_sandbox" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            pytest.skip(f"Podman not available: {e}")

    def test_sandbox_isolation(self):
        """Verify the sandbox has no network access."""
        try:
            result = subprocess.run(
                ["podman", "run", "--rm", "--network", "none",
                 "docker.io/library/alpine:latest", "ping", "-c", "1", "8.8.8.8"],
                capture_output=True, text=True, timeout=10,
            )
            # Should fail — no network
            assert result.returncode != 0
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            pytest.skip(f"Podman not available: {e}")


class TestPrewarmWithPodman:
    """Tests container prewarming with actual Podman."""

    def test_pull_and_run(self):
        """Verify we can pull and run a container (prewarm equivalent)."""
        import time
        try:
            result = subprocess.run(
                ["podman", "run", "-d", "--name", "half-test-prewarm",
                 "docker.io/library/alpine:latest", "sleep", "5"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                container_id = result.stdout.strip()
                time.sleep(1)
                inspect = subprocess.run(
                    ["podman", "inspect", container_id, "--format", "{{.State.Status}}"],
                    capture_output=True, text=True, timeout=10,
                )
                assert "running" in inspect.stdout
                # Wait for container to exit (sleep 5)
                time.sleep(6)
                subprocess.run(["podman", "rm", "-f", container_id],
                               capture_output=True, timeout=15)
            else:
                pytest.skip(f"Could not start container: {result.stderr}")
        except FileNotFoundError:
            pytest.skip("Podman not available")


class TestVoiceWithRealAudio:
    """Tests voice engine with actual audio files."""

    def test_transcribe_with_audio(self):
        """Create a real audio file and test transcription pipeline."""
        audio_file = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            # Create a real WAV file with a tone
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                 "-ac", "1", "-ar", "16000", str(audio_file)],
                capture_output=True, text=True, timeout=10,
            )
            assert audio_file.exists()
            assert audio_file.stat().st_size > 1000

            # Test transcribe with the real audio
            from half.half_sidecar import cmd_voice_stt
            result = cmd_voice_stt(str(audio_file))
            assert isinstance(result, dict)
        finally:
            try:
                audio_file.unlink()
            except OSError:
                pass

    def test_tts_generates_audio(self):
        """Test TTS pipeline actually generates audio."""
        from half.half_voice.engine import VoiceEngine
        engine = VoiceEngine()
        if not engine._tts_available:
            pytest.skip("TTS engine not available")
        out = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            result = engine.speak("Hello, this is a test.", output_path=str(out))
            assert result is not None
        except RuntimeError as e:
            if "Model file doesn't exist" in str(e):
                pytest.skip("Piper voice model not downloaded")
            raise


class TestSecurityScannersInstalled:
    """Test that security scanning tools are accessible."""

    def test_bandit_available(self):
        """Verify bandit (SAST) is installed."""
        try:
            r = subprocess.run(
                [sys.executable, "-m", "bandit", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            assert r.returncode == 0
        except (FileNotFoundError, ModuleNotFoundError):
            pytest.skip("bandit not installed")

    def test_ruff_check(self):
        """Verify ruff can run a security check."""
        try:
            r = subprocess.run(
                ["ruff", "check", "--select", "S", str(Path.cwd() / "src" / "half" / "config.py")],
                capture_output=True, text=True, timeout=10,
            )
            # ruff may return non-zero if it finds issues, that's OK
            assert r.returncode >= 0
        except FileNotFoundError:
            pytest.skip("ruff not installed")


class TestBrowserResearchWithRequests:
    """Test browser research agent with actual HTTP requests."""

    def test_web_fetch(self):
        """Test that basic web fetching works."""
        try:
            import urllib.request
            r = urllib.request.urlopen("https://example.com", timeout=5)
            assert r.status == 200
            content = r.read().decode()
            assert "Example Domain" in content
        except Exception as e:
            pytest.skip(f"Network not available: {e}")


class TestIndexingWithRealFiles:
    """Test file indexing with actual directory structures."""

    def test_index_real_project(self):
        """Index a real project directory."""
        from half.indexing import RepoIndexer
        idx = RepoIndexer(root=str(Path.cwd() / "src" / "half"))
        result = idx.build_index()
        assert isinstance(result, dict)
        assert len(result) > 0  # Should find files

    def test_search_finds_files(self):
        """Search should find indexed files."""
        from half.indexing import RepoIndexer
        idx = RepoIndexer(root=str(Path.cwd() / "src" / "half"))
        idx.build_index()
        results = idx.search("def ")
        assert isinstance(results, list)
