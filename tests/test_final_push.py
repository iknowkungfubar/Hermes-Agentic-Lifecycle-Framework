"""Targeted tests for remaining uncovered modules — pushing to 90%+."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile

import pytest


@pytest.fixture(autouse=True)
def _cleanup_db():
    """Clean up database singleton after each test."""
    yield
    from half.agent_mail.database import cleanup_db

    cleanup_db()


# ═══════════════════════════════════════════════════════════════════════════════
# half/__main__.py — CLI coverage (31% → 85%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLIMainAllPaths:
    """Test ALL argument parsing paths in main()."""

    def test_main_with_version_flag(self):
        """main() with --version should print version."""
        # Capture stdout
        import io
        import sys

        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "--version"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            assert "HALF v1.0.0" in output
        finally:
            sys.stdout = old_stdout

    def test_main_with_no_args(self):
        """main() with no args should show help."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            assert "usage:" in output.lower()
        finally:
            sys.stdout = old_stdout

    def test_main_with_status(self):
        """main() with status should produce JSON output."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "status"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            data = json.loads(output)
            assert "status" in data
        finally:
            sys.stdout = old_stdout

    def test_main_with_version_command(self):
        """main() with version should print version."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "version"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            assert "HALF v1.0.0" in output
        finally:
            sys.stdout = old_stdout

    def test_main_with_init(self):
        """main() with init should dispatch to genesis."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = [
                "half",
                "init",
                "--project",
                "testp",
                "--mode",
                "full",
                "--dir",
                "/tmp/half-test-init",
            ]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            # Should produce JSON output with project info
            assert "testp" in output or "project" in output or "status" in output
        finally:
            sys.stdout = old_stdout

    def test_main_with_run_phase(self):
        """main() with run-phase should dispatch."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "run-phase", "phase-1"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            data = json.loads(output)
            assert data["status"] == "started"
        finally:
            sys.stdout = old_stdout

    def test_main_with_gate_check(self):
        """main() with gate-check should dispatch."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "gate-check", "phase-1"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            data = json.loads(output)
            assert "status" in data
        finally:
            sys.stdout = old_stdout

    def test_main_with_generate_mrp(self):
        """main() with generate-mrp should dispatch."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "generate-mrp"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            data = json.loads(output)
            assert "checks" in data
        finally:
            sys.stdout = old_stdout

    def test_main_with_focalboard_create(self):
        """main() with focalboard create should dispatch."""
        from half.__main__ import main

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            sys.argv = ["half", "focalboard", "create"]
            with contextlib.suppress(SystemExit):
                main()
            output = captured.getvalue()
            data = json.loads(output)
            assert "status" in data
        finally:
            sys.stdout = old_stdout

    def test_main_with_unknown_command(self):
        """main() with unknown command should print error."""
        from half.__main__ import main

        captured = io.StringIO()
        captured_err = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured
        sys.stderr = captured_err
        try:
            sys.argv = ["half", "nonexistent_cmd_xyz123"]
            with contextlib.suppress(SystemExit):
                main()
            err_output = captured_err.getvalue()
            assert "Error" in err_output or "error" in err_output
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


# ═══════════════════════════════════════════════════════════════════════════════
# agents/specification.py (62% → 85%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSpecificationDetailed:
    """Test specification agent render and edge case methods."""

    def test_add_nfr(self):
        """Adding NFR should assign ID."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        nfr = agent.add_non_functional_requirement(
            "security", "All traffic must be encrypted", "TLS 1.3"
        )
        assert nfr.id == "NFR-001"
        assert nfr.category == "security"

    def test_add_api_contract(self):
        """Adding API contract should store it."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        contract = agent.add_api_contract(
            "POST",
            "/api/users",
            {"name": "string"},
            {"id": "uuid"},
            [{"code": 400, "description": "Bad request"}],
        )
        assert contract.method == "POST"
        assert contract.path == "/api/users"
        assert len(contract.error_codes) == 1

    def test_render_spec_markdown(self):
        """Rendering spec should include FRs and NFRs."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        agent.add_functional_requirement("Login", "User login", "P0")
        agent.add_non_functional_requirement("perf", "Fast response", "<200ms")
        agent.add_api_contract("GET", "/health", {}, {"status": "ok"})
        md = agent.render_specification_markdown()
        assert "Functional Requirements" in md
        assert "FR-001" in md
        assert "Non-Functional Requirements" in md
        assert "API Contracts" in md
        assert "GET /health" in md

    def test_render_tasks_markdown(self):
        """Rendering tasks should include dependency graph."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        agent.add_functional_requirement("Auth", "Auth system", "P0")
        agent.add_functional_requirement(
            "Profile", "User profile", "P1", depends_on=["FR-001"]
        )
        agent.decompose_tasks()
        md = agent.render_tasks_markdown()
        assert "Task Decomposition" in md
        assert "T-001" in md
        assert "graph TD" in md or "mermaid" in md


# ═══════════════════════════════════════════════════════════════════════════════
# agents/testing.py (56% → 85%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestTestingDetailed:
    """Test testing agent remaining paths."""

    def test_record_happy_path(self):
        """Recording happy path test should mark FR."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")
        agent.record_happy_path("FR-001", "test_login_success")
        assert agent.coverage["FR-001"].happy_path_test is True

    def test_record_error_test(self):
        """Recording error test should add to list."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")
        agent.record_error_test("FR-001", "test_login_invalid_password")
        assert len(agent.coverage["FR-001"].error_condition_tests) == 1

    def test_record_edge_case(self):
        """Recording edge case test should add to list."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")
        agent.record_edge_case("FR-001", "test_login_max_attempts")
        assert len(agent.coverage["FR-001"].edge_case_tests) == 1

    def test_generate_quality_report_with_gaps(self):
        """Quality report should identify gaps."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")  # No tests recorded — should be a gap
        agent.add_fr("FR-002")
        agent.record_happy_path("FR-002", "test_success")
        agent.record_error_test("FR-002", "test_error")
        report = agent.generate_quality_report()
        assert report.total_frs == 2
        assert report.fr_coverage >= 0
        assert "FR-001" in str(report.gap_frs) or len(report.gap_frs) > 0

    def test_derive_tests_from_fr(self):
        """Deriving tests from FR should return sensible names."""
        from half.agents.testing import TestingAgent

        tests = TestingAgent.derive_tests_from_fr("FR-001", "User registration")
        assert len(tests) >= 3
        assert any("success" in t for t in tests)
        assert any("invalid" in t for t in tests)

    def test_derive_tests_from_auth_fr(self):
        """Auth-related FRs should get auth-specific tests."""
        from half.agents.testing import TestingAgent

        tests = TestingAgent.derive_tests_from_fr("FR-002", "User login with auth")
        auth_tests = [
            t for t in tests if "token" in t or "password" in t or "rate" in t
        ]
        assert len(auth_tests) > 0

    def test_render_report_with_coverage(self):
        """Render report should include summary."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")
        agent.record_happy_path("FR-001", "test_ok")
        report = agent.generate_quality_report()
        md = agent.render_report_markdown(report)
        assert "Test Quality Report" in md
        assert "FR-001" in md


# ═══════════════════════════════════════════════════════════════════════════════
# half_sidecar.py (66% → 85%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSidecarRemaining:
    """Test remaining sidecar command handlers."""

    def test_voice_stt_returns_error_for_bad_file(self):
        """Voice STT with nonexistent file should return error dict."""
        from half.half_sidecar import cmd_voice_stt

        result = cmd_voice_stt("/tmp/half_nonexistent_test_file.wav")
        assert isinstance(result, dict)
        assert "status" in result

    def test_voice_tts_returns_dict(self):
        """Voice TTS should return dict."""
        from half.half_sidecar import cmd_voice_tts

        result = cmd_voice_tts("Hello world test message")
        assert isinstance(result, dict)
        assert "status" in result

    def test_status_returns_expected_structure(self):
        """Status should have all expected keys."""
        from half.half_sidecar import cmd_status

        result = cmd_status()
        expected_keys = {
            "status",
            "project",
            "mode",
            "completed_phases",
            "active_phase",
            "error_budget_remaining",
        }
        assert expected_keys.issubset(result.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# half_voice/engine.py (58% → 80%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestVoiceCoverage:
    """Voice engine — remaining uncovered paths."""

    def test_init_with_custom_device(self):
        """Engine should accept custom compute device."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine(device="cpu")
        assert engine.device == "cpu"

    def test_which_returns_empty_for_missing(self):
        """_which should return empty for missing commands."""
        from half.half_voice import VoiceEngine

        result = VoiceEngine._which("nonexistent_command_xyz_123")
        assert result == ""

    def test_speak_raises_without_piper(self):
        """Speak should raise RuntimeError if piper unavailable."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine(piper_exec="")
        with pytest.raises(RuntimeError, match="TTS unavailable"):
            engine.speak("test")

    def test_transcribe_raises_without_whisper(self):
        """Transcribe should raise RuntimeError if whisper unavailable."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine(whisper_exec="")
        with pytest.raises(RuntimeError, match="STT unavailable"):
            engine.transcribe("/tmp/test.wav")


# ═══════════════════════════════════════════════════════════════════════════════
# agent_mail/server.py (44% → 80%+)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentMailServer:
    """Test MCP server tool functions directly."""

    def test_register_agent_tool(self):
        """Register agent tool should work."""
        from half.agent_mail.server import register_agent

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                result = register_agent(name="test-agent", role="tester")
                assert result["status"] == "registered"
                assert "test-agent@half.local" in result["email"]
            finally:
                os2.chdir(orig)

    def test_list_agents_tool(self):
        """List agents tool should return list."""
        from half.agent_mail.server import list_agents

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                agents = list_agents()
                assert isinstance(agents, list)
            finally:
                os2.chdir(orig)

    def test_send_and_get_messages(self):
        """Send then get messages should return them."""
        from half.agent_mail.server import get_messages, register_agent, send_message

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("sender1", "coder")
                register_agent("receiver1", "reviewer")
                send_result = send_message(
                    sender="sender1@half.local",
                    recipients="receiver1@half.local",
                    subject="Test",
                    body="Hello!",
                )
                assert send_result["status"] == "sent"
                msgs = get_messages(agent_email="receiver1@half.local")
                assert len(msgs) >= 1
                assert msgs[0]["subject"] == "Test"
            finally:
                os2.chdir(orig)

    def test_mark_read_tool(self):
        """Mark read tool should work."""
        from half.agent_mail.server import (
            get_messages,
            mark_read,
            register_agent,
            send_message,
        )

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("alice", "coder")
                register_agent("bob", "reviewer")
                result = send_message(
                    "alice@half.local", "bob@half.local", "Read test", "Body"
                )
                mark_read(result["message_id"])
                msgs = get_messages("bob@half.local", unread_only=True)
                assert len(msgs) == 0  # All read
            finally:
                os2.chdir(orig)

    def test_get_thread_tool(self):
        """Get thread tool should return messages."""
        from half.agent_mail.server import get_thread, register_agent, send_message

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("a", "coder")
                register_agent("b", "reviewer")
                msg1 = send_message("a@half.local", "b@half.local", "Thread1", "First")
                send_message(
                    "b@half.local",
                    "a@half.local",
                    "Re: Thread1",
                    "Second",
                    thread_id=msg1["thread_id"],
                    in_reply_to=msg1["message_id"],
                )
                thread = get_thread(msg1["thread_id"])
                assert len(thread) >= 2
            finally:
                os2.chdir(orig)

    def test_acquire_and_release_lease_tool(self):
        """Acquire and release lease through tools."""
        from half.agent_mail.server import acquire_lease, register_agent, release_lease

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("dev1", "coder")
                lease = acquire_lease("src/main.py", "dev1@half.local", "Refactoring")
                assert lease["status"] == "acquired"
                release = release_lease(lease["lease_id"], "dev1@half.local")
                assert release["status"] == "released"
            finally:
                os2.chdir(orig)

    def test_get_active_leases_tool(self):
        """Get active leases through tools."""
        from half.agent_mail.server import (
            acquire_lease,
            get_active_leases,
            register_agent,
        )

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("dev1", "coder")
                acquire_lease("src/a.py", "dev1@half.local", "Work")
                leases = get_active_leases(agent_email="dev1@half.local")
                assert len(leases) == 1
                assert leases[0]["file_path"] == "src/a.py"
            finally:
                os2.chdir(orig)

    def test_lease_conflict_tool(self):
        """Lease conflict should return conflict status."""
        from half.agent_mail.server import acquire_lease, register_agent

        with tempfile.TemporaryDirectory() as tmp:
            import os as os2

            orig = os2.getcwd()
            os2.chdir(tmp)
            try:
                register_agent("dev1", "coder")
                register_agent("dev2", "coder")
                acquire_lease("src/conflict.py", "dev1@half.local", "First")
                conflict = acquire_lease(
                    "src/conflict.py", "dev2@half.local", "Conflict"
                )
                assert conflict["status"] == "conflict"
            finally:
                os2.chdir(orig)


class TestPhase5GateWithMonitoring:
    """TDD: Phase 5 gate should pass when monitoring config exists."""

    def test_phase_5_gate_passes_with_monitoring(self):
        """Phase 5 gate should return passed=True when monitoring config is present."""
        import os
        import tempfile
        from pathlib import Path

        from half.runtime.nodes import phase_5_gate
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            # Create monitoring config where phase_5_gate expects it
            halve = Path(tmp) / ".hale"
            phase5_dir = halve / "artifacts" / "phase-5"
            phase5_dir.mkdir(parents=True)
            (phase5_dir / "monitoring-config.yaml").write_text(
                "monitoring:\n  enabled: true\n"
            )

            orig = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_5_gate(state)
                gate = result["gate_results"][0]
                assert gate["passed"] is True, (
                    f"Phase 5 gate should pass with monitoring config, got: {gate}"
                )
            finally:
                os.chdir(orig)

    def test_phase_5_gate_fails_without_monitoring(self):
        """Phase 5 gate should return passed=False when monitoring config is missing."""
        import os
        import tempfile

        from half.runtime.nodes import phase_5_gate
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            orig = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_5_gate(state)
                gate = result["gate_results"][0]
                assert gate["passed"] is False, (
                    f"Phase 5 gate should fail without monitoring config, got: {gate}"
                )
            finally:
                os.chdir(orig)
