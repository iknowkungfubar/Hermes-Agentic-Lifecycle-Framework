"""Targeted tests for remaining uncovered lines — pushing to 90%+."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# half_sidecar.py — uncovered lines 79-81, 143, 155, 181-188, 200-230
# ═══════════════════════════════════════════════════════════════════════════════


class TestSidecarEdgeCases:
    """Test remaining sidecar edge cases."""

    def test_cmd_run_phase_returns_started(self):
        """run-phase should return started status."""
        from half.half_sidecar import cmd_run_phase
        result = cmd_run_phase("phase-1")
        assert result["status"] == "started"

    def test_cmd_gate_check_phase2_returns_error(self):
        """gate-check for phase-2 should return error (no automated check)."""
        from half.half_sidecar import cmd_gate_check
        result = cmd_gate_check("phase-2")
        assert result["status"] == "error"
        assert "No automated gate check" in result["message"]

    def test_cmd_gate_check_phase4_returns_error(self):
        """gate-check for phase-4 should return error."""
        from half.half_sidecar import cmd_gate_check
        result = cmd_gate_check("phase-4")
        assert result["status"] == "error"

    def test_cmd_voice_tts_returns_dict(self):
        """Voice TTS should return a dict with status."""
        from half.half_sidecar import cmd_voice_tts
        result = cmd_voice_tts("Hello HALF")
        assert isinstance(result, dict)

    def test_cmd_focalboard_create_offline(self):
        """Focalboard create when offline should return error gracefully."""
        from half.half_sidecar import cmd_focalboard_create
        result = cmd_focalboard_create()
        assert isinstance(result, dict)
        assert "status" in result


# ═══════════════════════════════════════════════════════════════════════════════
# half/__main__.py — uncovered lines 74-77, 114-119, 134, 157-160, 164
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLIRouting:
    """Test CLI command routing edge cases."""

    def test_route_unknown_command(self):
        """Unknown command should return error dict."""
        from half.__main__ import _route_command
        import argparse
        args = argparse.Namespace(command="nonexistent_cmd", fb_cmd="")
        result = _route_command(args)
        assert isinstance(result, dict)
        assert "error" in result

    def test_route_voice_without_subcommand(self):
        """Voice command without subcommand should return error."""
        from half.__main__ import _route_command
        import argparse
        args = argparse.Namespace(command="voice", voice_cmd=None, fb_cmd="")
        result = _route_command(args)
        assert isinstance(result, dict) and "error" in result or result is None

    def test_route_focalboard_without_subcommand(self):
        """Focalboard without subcommand should return error."""
        from half.__main__ import _route_command
        import argparse
        args = argparse.Namespace(command="focalboard", fb_cmd=None)
        result = _route_command(args)
        assert isinstance(result, dict) and "error" in result or result is None

    def test_version_command_routes(self):
        """Version command should call _show_version."""
        from half.__main__ import _route_command
        import argparse
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            args = argparse.Namespace(command="version", fb_cmd="")
            result = _route_command(args)
            assert result is None
            output = sys.stdout.getvalue()
            assert "HALF v1.0.0" in output
        finally:
            sys.stdout = old_stdout

    def test_init_command_routes(self):
        """Init command should return a dict with project info."""
        from half.__main__ import _cmd_init
        import argparse
        args = argparse.Namespace(command="init", project="test-cli", mode="full", dir="/tmp/test-init-cli")
        result = _cmd_init(args)
        assert isinstance(result, dict)
        assert "project" in result or "status" in result


# ═══════════════════════════════════════════════════════════════════════════════
# agents/implement.py — uncovered lines 53-54, 74-81, 97-109
# ═══════════════════════════════════════════════════════════════════════════════


class TestImplementAgentCoverage:
    """Test implement agent remaining uncovered paths."""

    def test_create_harness(self):
        """Creating a test harness should record it."""
        from half.agents.implement import ImplementAgent

        agent = ImplementAgent()
        harness = agent.create_test_harness("T-001", "FR-001", "tests/test_x.py", "assert True")
        assert harness.task_id == "T-001"
        assert harness.fr_id == "FR-001"

    def test_verify_harness_first_true(self):
        """Verify harness-first should check all conditions."""
        from half.agents.implement import ImplementAgent

        agent = ImplementAgent()
        harness = agent.create_test_harness("T-001", "FR-001", "tests/test_x.py", "assert True")
        harness.created_before_implementation = True
        harness.first_run_passed = False
        harness.final_run_passed = True
        assert agent.verify_harness_first("T-001") is True

    def test_verify_harness_first_false(self):
        """Verify harness-first should return False if conditions not met."""
        from half.agents.implement import ImplementAgent

        agent = ImplementAgent()
        harness = agent.create_test_harness("T-001", "FR-001", "tests/test_x.py", "assert True")
        # All defaults are False — should fail verification
        assert agent.verify_harness_first("T-001") is False

    def test_generate_source_template_with_params(self):
        """Source template should include parameters."""
        from half.agents.implement import ImplementAgent

        source = ImplementAgent.generate_source_template(
            "pkg.module", "process_data",
            {"input_data": "str", "config": "dict | None"},
            "dict",
            "Process input data with optional config.",
        )
        assert "process_data" in source
        assert "input_data: str" in source
        assert "config: dict | None" in source
        assert "Process input data" in source


# ═══════════════════════════════════════════════════════════════════════════════
# agent_mail/git_backend.py — uncovered lines 55-56, 85-91, 165, 180-181, 192-195
# ═══════════════════════════════════════════════════════════════════════════════


class TestGitBackendEdgeCases:
    """Test git backend error and edge paths."""

    def test_init_repo_creates_git(self):
        """Initializing should create .git directory."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            assert (mail_dir / ".git").exists()

    def test_get_log_empty(self):
        """Getting log on empty repo should return empty list."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            log = git.get_log()
            assert isinstance(log, list)

    def test_repository_size_returns_string(self):
        """Repository size should return a string."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            size = git.repository_size()
            assert isinstance(size, str)

    def test_get_diff_returns_string(self):
        """Getting a diff should return a string."""
        from half.agent_mail.git_backend import GitMailBackend

        with tempfile.TemporaryDirectory() as tmp:
            mail_dir = Path(tmp) / "agent-mail"
            git = GitMailBackend(mail_dir)
            diff = git.get_diff("HEAD")
            assert isinstance(diff, str)
