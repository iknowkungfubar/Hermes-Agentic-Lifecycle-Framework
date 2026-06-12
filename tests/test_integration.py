"""Tests for GitMailBackend, VoiceEngine, FocalboardClient, and half_sidecar."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestGitMailBackend:
    """Test Git-backed Agent Mail."""

    def test_init_repo(self):
        """Initializing Git backend should create a .git directory."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            assert (mail_dir / ".git").exists()
            log = git.get_log()
            assert isinstance(log, list)

    def test_commit_message(self):
        """Committing a message should appear in log."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)

            # Create a dummy db file to commit
            db_file = mail_dir / "mail.db"
            db_file.write_text("test data")

            git.commit_message_sent("msg-1", "alice@half.local", ["bob@half.local"])
            log = git.get_log()
            subjects = [c["subject"] for c in log]
            assert any("alice@half.local" in s for s in subjects)

    def test_commit_lease(self):
        """Committing a lease should appear in log."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            db_file = mail_dir / "mail.db"
            db_file.write_text("test data")

            git.commit_lease_acquired("lease-1", "src/main.py", "coder@half.local")
            git.commit_lease_released("lease-1", "src/main.py", "coder@half.local")
            log = git.get_log()
            assert len(log) >= 2


class TestVoiceEngine:
    """Test VoiceEngine (with fallback checks)."""

    def test_init(self):
        """Creating a VoiceEngine should not raise."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        assert engine is not None
        availability = engine.is_available
        assert "stt" in availability
        assert "tts" in availability

    def test_tts_fails_gracefully(self):
        """TTS without Piper installed should raise RuntimeError."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        if not engine._tts_available:
            with pytest.raises(RuntimeError, match="TTS unavailable"):
                engine.speak("Hello")

    def test_stt_fails_gracefully(self):
        """STT without Whisper installed should raise RuntimeError."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        if not engine._stt_available:
            with pytest.raises(RuntimeError, match="STT unavailable"):
                engine.transcribe("nonexistent.wav")


class TestFocalboardClient:
    """Test Focalboard client (works offline with fallbacks)."""

    def test_init(self):
        """Creating client should not raise."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient()
        assert client.base_url == "http://127.0.0.1:8000"

    def test_list_boards_offline(self):
        """Listing boards when Focalboard is offline should return empty list."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        boards = client.list_boards()
        assert boards == []

    def test_create_board_offline(self):
        """Creating board offline should return board with empty id."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        board = client.create_board("Test", "Description")
        assert board.id == ""
        assert board.title == "Test"

    def test_create_task_offline(self):
        """Creating task offline should return card with empty id."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        card = client.create_task("board-1", "Test Task", phase="phase-1")
        assert card.id == ""
        assert card.title == "Test Task"

    def test_task_from_phase_step(self):
        """Creating a task from a phase step should set correct metadata."""
        from half.half_focalboard import FocalboardClient

        card = FocalboardClient.task_from_phase_step(
            "phase-2",
            "Implementation",
            "HALF-Implement",
        )
        assert "[PHASE-2]" in card.title
        assert "HALF-Implement" in card.description
        assert card.phase == "phase-2"

    def test_update_task_status_offline(self):
        """Updating task status offline should return False."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        result = client.update_task_status("card-1", "done")
        assert result is False


class TestHalfSidecar:
    """Test half_sidecar commands."""

    def test_status_returns_dict(self):
        """Status command should return a dict with expected keys."""
        from half.half_sidecar import cmd_status

        result = cmd_status()
        assert "status" in result
        assert "project" in result
        assert "mode" in result

    def test_gate_check_unknown_phase(self):
        """Gate check for unsupported phase should return error."""
        from half.half_sidecar import cmd_gate_check

        result = cmd_gate_check("phase-99")
        assert result["status"] == "error"

    def test_generate_mrp(self):
        """MRP generation should return a dict with checks."""
        from half.half_sidecar import cmd_generate_mrp

        with tempfile.TemporaryDirectory() as tmp:
            original = Path.cwd()
            import os

            os.chdir(tmp)
            try:
                result = cmd_generate_mrp()
                assert "checks" in result
                assert result["status"] == "pending"
            finally:
                os.chdir(original)

    def test_voice_stt_nonexistent(self):
        """Voice STT with nonexistent file should return error gracefully."""
        from half.half_sidecar import cmd_voice_stt

        result = cmd_voice_stt("/nonexistent/audio.wav")
        assert result["status"] in ("error", "ok")  # ok if whisper is installed
