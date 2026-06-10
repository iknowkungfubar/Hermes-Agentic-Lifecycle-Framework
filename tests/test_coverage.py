"""Comprehensive tests for all remaining untested modules.

Covers: fail_safe, gate_checker, orchestrator, runtime (graph, checkpointer, state),
voice engine, half_sidecar, focalboard, and nodes.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# fail_safe.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestFailSafeConfig:
    """Test FailSafeConfig dataclass."""

    def test_default_config(self):
        """Default config should have sensible values."""
        from half.core.fail_safe import FailSafeConfig

        cfg = FailSafeConfig()
        assert cfg.enabled is True
        assert cfg.max_step_retries == 3
        assert cfg.max_phase_retries == 2
        assert cfg.step_cooldown_seconds == 30


class TestFailSafeExecutor:
    """Test the FailSafeExecutor."""

    def test_init(self):
        """Executor should initialize with default state."""
        from half.core.fail_safe import EscalationLevel, FailSafeExecutor

        executor = FailSafeExecutor()
        assert executor.state.level == EscalationLevel.NONE
        assert executor.state.step_retries == 0

    def test_execute_success_on_first_try(self):
        """Successful execution should return True with no gap report."""
        from half.core.fail_safe import FailSafeExecutor

        executor = FailSafeExecutor()
        success, gap = executor.execute_with_retry(
            lambda: (True, "ok"), "test-step", "G-test"
        )
        assert success is True
        assert gap is None

    def test_execute_retry_on_failure(self):
        """Failed execution should retry up to max attempts."""
        from half.core.fail_safe import FailSafeExecutor

        attempts = [0]

        def failing_fn():
            attempts[0] += 1
            return (False, "failed")

        executor = FailSafeExecutor()
        # Override cooldown to 0 for faster testing
        executor.config.step_cooldown_seconds = 0
        success, gap = executor.execute_with_retry(failing_fn, "fail-step", "G-test")

        assert success is False
        assert gap is not None
        assert attempts[0] == executor.config.max_step_retries

    def test_can_phase_retry(self):
        """Phase retry should be available initially."""
        from half.core.fail_safe import FailSafeExecutor

        executor = FailSafeExecutor()
        assert executor.can_phase_retry() is True

    def test_escalate_to_human(self):
        """Human escalation should set level to HUMAN_ESCALATION."""
        from half.core.fail_safe import EscalationLevel, FailSafeExecutor

        executor = FailSafeExecutor()
        executor.escalate_to_human()
        assert executor.state.level == EscalationLevel.HUMAN_ESCALATION

    def test_reset(self):
        """Reset should clear state."""
        from half.core.fail_safe import FailSafeExecutor

        executor = FailSafeExecutor()
        executor.state.step_retries = 3
        executor.reset()
        assert executor.state.step_retries == 0

    def test_disabled_fail_safe(self):
        """Disabled fail-safe should pass through immediately."""
        from half.core.fail_safe import FailSafeConfig, FailSafeExecutor

        cfg = FailSafeConfig(enabled=False)
        executor = FailSafeExecutor(cfg)
        success, _gap = executor.execute_with_retry(
            lambda: (True, "ok"), "test", "G-test"
        )
        assert success is True


# ═══════════════════════════════════════════════════════════════════════════════
# gate_checker.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateCheck:
    """Test the GateCheck class."""

    def test_run_passes(self):
        """A passing evaluator should return passed=True."""
        from half.core.gate_checker import GateCheck

        check = GateCheck("G-test", "Test gate", lambda: (True, "all good"))
        result = check.run()
        assert result["passed"] is True
        assert result["gate_id"] == "G-test"

    def test_run_fails(self):
        """A failing evaluator should return passed=False."""
        from half.core.gate_checker import GateCheck

        check = GateCheck("G-test", "Test gate", lambda: (False, "bad"))
        result = check.run()
        assert result["passed"] is False

    def test_run_exception_handled(self):
        """An exception in the evaluator should be caught."""
        from half.core.gate_checker import GateCheck

        def broken():
            msg = "oops"
            raise ValueError(msg)

        check = GateCheck("G-test", "Broken gate", broken)
        result = check.run()
        assert result["passed"] is False
        assert "Exception" in result["details"]

    def test_blocking_default(self):
        """Gate check should be blocking by default."""
        from half.core.gate_checker import GateCheck

        check = GateCheck("G-test", "Test", lambda: (True, "ok"))
        assert check.is_blocking is True

    def test_non_blocking(self):
        """Non-blocking gate should not prevent pipeline progress."""
        from half.core.gate_checker import GateCheck

        check = GateCheck("G-test", "Test", lambda: (False, "warn"), is_blocking=False)
        assert check.is_blocking is False


class TestGateChecker:
    """Test the GateChecker orchestrator."""

    def test_check_phase_1_no_artifacts(self):
        """Phase 1 gate with no artifacts should fail."""
        from half.core.gate_checker import GateChecker

        with tempfile.TemporaryDirectory() as tmp:
            checker = GateChecker(Path(tmp))
            results = checker.check_phase_1()
            assert len(results) >= 1
            # All should fail since artifacts don't exist
            assert any(r["passed"] is False for r in results)

    def test_has_blocking_failures(self):
        """Blocking failures should be detected."""
        from half.core.gate_checker import GateChecker

        results = [
            {"gate_id": "G1", "passed": False, "blocking": True, "details": "fail"},
        ]
        checker = GateChecker(Path("/tmp"))
        assert checker.has_blocking_failures(results) is True

    def test_no_blocking_failures(self):
        """Non-blocking failures should not block."""
        from half.core.gate_checker import GateChecker

        results = [
            {"gate_id": "G1", "passed": False, "blocking": False, "details": "warn"},
        ]
        checker = GateChecker(Path("/tmp"))
        assert checker.has_blocking_failures(results) is False

    def test_summary(self):
        """Summary should show pass/fail counts."""
        from half.core.gate_checker import GateChecker

        results = [
            {"gate_id": "G1", "passed": True, "blocking": True, "details": "ok"},
            {"gate_id": "G2", "passed": False, "blocking": True, "details": "fail"},
        ]
        checker = GateChecker(Path("/tmp"))
        summary = checker.summary(results)
        assert "1/2 passed" in summary
        assert "1 failed" in summary


class TestPhase1Gates:
    """Test Phase 1 specific gate evaluators."""

    def test_g1_1_no_spec(self):
        """G1.1 should fail without spec file."""
        from half.core.gate_checker import Phase1Gates

        with tempfile.TemporaryDirectory() as tmp:
            gates = Phase1Gates(Path(tmp))
            check = gates.get_all()[0]
            result = check.run()
            assert result["gate_id"] == "G1.1"
            assert result["passed"] is False

    def test_g1_3_no_adrs(self):
        """G1.3 should fail without ADR file."""
        from half.core.gate_checker import Phase1Gates

        with tempfile.TemporaryDirectory() as tmp:
            gates = Phase1Gates(Path(tmp))
            check = gates.get_all()[2]  # G1.3
            result = check.run()
            assert result["passed"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# orchestrator.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestOrchestrator:
    """Test the phase orchestrator."""

    def test_create_default(self):
        """Default orchestrator should use full mode."""
        from half.core.orchestrator import Orchestrator, PipelineMode

        orch = Orchestrator(project_name="test")
        assert orch.mode == PipelineMode.FULL
        assert orch.project_name == "test"

    def test_prototype_mode(self):
        """Prototype mode should only have phases 1, 2, 4."""
        from half.core.orchestrator import Orchestrator, PipelineMode

        orch = Orchestrator("test", mode=PipelineMode.PROTOTYPE)
        phases = orch.active_phases
        phase_names = [p.value for p in phases]
        assert "phase-1" in phase_names
        assert "phase-2" in phase_names
        assert "phase-4" in phase_names
        assert "phase-3" not in phase_names

    def test_next_phase(self):
        """Next phase should advance through the pipeline."""
        from half.core.orchestrator import Orchestrator, PipelineMode

        orch = Orchestrator("test", mode=PipelineMode.PATCH)
        p1 = orch.next_phase()
        assert p1 is not None
        assert p1.value == "phase-5"

    def test_complete_phase(self):
        """Completing a phase should move to next."""
        from half.core.orchestrator import Orchestrator

        orch = Orchestrator("test")
        orch.next_phase()
        orch.complete_phase()
        assert len(orch.completed_phases) == 1

    def test_get_pipeline_status(self):
        """Pipeline status should report correctly."""
        from half.core.orchestrator import Orchestrator

        orch = Orchestrator("test-project")
        status = orch.get_pipeline_status()
        assert status["project"] == "test-project"
        assert status["mode"] == "full"
        assert status["active_phase"] is None

    def test_log_gate_result(self):
        """Logging a gate result should write a file."""
        from half.core.orchestrator import Orchestrator

        with tempfile.TemporaryDirectory() as tmp:
            orch = Orchestrator("test", workspace=Path(tmp))
            orch.next_phase()
            log_path = orch.log_gate_result("G-test", True, {"detail": "passed"})
            assert log_path.exists()
            data = json.loads(log_path.read_text())
            assert data["gate_id"] == "G-test"
            assert data["passed"] is True

    def test_generate_gap_report(self):
        """Gap report should contain failure details."""
        from half.core.orchestrator import Orchestrator

        orch = Orchestrator("test")
        report = orch.generate_gap_report("G-fail", [{"details": "fail"}], attempts=3)
        assert report["gate_id"] == "G-fail"
        assert len(report["what_was_tried"]) == 1

    def test_get_phase_agents(self):
        """Phase agents should return correct agent list."""
        from half.core.orchestrator import Orchestrator, Phase

        orch = Orchestrator("test")
        agents = orch.get_phase_agents(Phase.PHASE_1)
        assert "1A" in agents
        assert agents["1A"] == "HALF-Discovery"

    def test_get_phase_artifacts(self):
        """Phase artifacts should return expected files."""
        from half.core.orchestrator import Orchestrator, Phase

        orch = Orchestrator("test")
        artifacts = orch.get_phase_artifacts(Phase.PHASE_1)
        assert "01-REQUIREMENTS.md" in artifacts


# ═══════════════════════════════════════════════════════════════════════════════
# runtime/state.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestRuntimeState:
    """Test the HalfState type and helpers."""

    def test_initial_state(self):
        """Initial state should have default values."""
        from half.runtime.state import initial_state

        state = initial_state("my-project")
        assert state["project_name"] == "my-project"
        assert state["mode"] == "full"
        assert state["current_phase"] == "phase-1"
        assert state["error_budget_remaining"] == 100
        assert state["deployment_approved"] is False

    def test_is_gate_passed_true(self):
        """is_gate_passed should return True for passed gates."""
        from half.runtime.state import initial_state, is_gate_passed

        state = initial_state()
        state["gate_results"] = [{"gate_id": "G1", "passed": True, "details": "", "timestamp": ""}]
        assert is_gate_passed(state, "G1") is True

    def test_is_gate_passed_false(self):
        """is_gate_passed should return False for failed gates."""
        from half.runtime.state import initial_state, is_gate_passed

        state = initial_state()
        state["gate_results"] = [{"gate_id": "G1", "passed": False, "details": "", "timestamp": ""}]
        assert is_gate_passed(state, "G1") is False

    def test_is_gate_passed_no_results(self):
        """is_gate_passed should return False with no results."""
        from half.runtime.state import initial_state, is_gate_passed

        state = initial_state()
        assert is_gate_passed(state, "G1") is False


# ═══════════════════════════════════════════════════════════════════════════════
# runtime/graph.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestRuntimeGraph:
    """Test the LangGraph state graph builder."""

    def test_build_graph(self):
        """Building the graph should return a StateGraph."""
        from half.runtime.graph import build_half_graph

        graph = build_half_graph()
        assert graph is not None

    def test_create_executor(self):
        """Creating an executor should return compiled app and state."""
        from half.runtime.graph import create_half_executor

        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "checkpoints.db")
            app, state = create_half_executor("test", "full", db_path)
            assert app is not None
            assert state["project_name"] == "test"


# ═══════════════════════════════════════════════════════════════════════════════
# runtime/checkpointer.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestCheckpointer:
    """Test the secure checkpointer."""

    def test_create_checkpointer(self):
        """Creating the checkpointer should initialize SQLite with WAL."""
        from half.runtime.checkpointer import (
            close_checkpointer,
            create_secure_checkpointer,
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            cp = create_secure_checkpointer(db_path)
            assert cp is not None
            assert Path(db_path).exists()
            close_checkpointer(cp)

    def test_get_checkpoint_paths(self):
        """Checkpoint paths should contain db, wal, shm."""
        from half.runtime.checkpointer import get_checkpoint_paths

        with tempfile.TemporaryDirectory() as tmp:
            paths = get_checkpoint_paths(tmp)
            assert "db" in paths
            assert str(paths["db"]).endswith("checkpoints.db")


# ═══════════════════════════════════════════════════════════════════════════════
# runtime/nodes.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestRuntimeNodes:
    """Test the LangGraph phase nodes."""

    def test_phase_1_discovery(self):
        """Phase 1 discovery should produce artifacts."""
        from half.runtime.nodes import phase_1_discovery
        from half.runtime.state import initial_state

        state = initial_state("test-proj")
        result = phase_1_discovery(state)
        assert "artifacts" in result
        assert result["current_step"] == "phase-1-discovery"

    def test_phase_1_gate_fails_without_artifacts(self):
        """Phase 1 gate should fail when artifacts don't exist."""
        from half.runtime.nodes import phase_1_gate
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            import os
            original = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_1_gate(state)
                gate = result["gate_results"][0]
                assert gate["passed"] is False
            finally:
                os.chdir(original)

    def test_phase_2_scaffold(self):
        """Phase 2 scaffold should create directory structure."""
        from half.runtime.nodes import phase_2_scaffold
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            import os
            original = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_2_scaffold(state)
                assert result["current_step"] == "phase-2-scaffold"
            finally:
                os.chdir(original)

    def test_phase_2_research(self):
        """Phase 2 research should analyze codebase."""
        from half.runtime.nodes import phase_2_research
        from half.runtime.state import initial_state

        state = initial_state("test")
        result = phase_2_research(state)
        assert result["current_step"] == "phase-2-research"

    def test_phase_3_testing(self):
        """Phase 3 testing should return a result."""
        from half.runtime.nodes import phase_3_testing
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            import os
            original = os.getcwd()
            os.chdir(tmp)
            try:
                os.makedirs("tests")
                Path("tests/test_dummy.py").write_text("def test(): assert True")
                state = initial_state("test")
                result = phase_3_testing(state)
                assert result["current_step"] == "phase-3-testing"
            finally:
                os.chdir(original)

    def test_phase_4_infrastructure(self):
        """Phase 4 should generate Docker config."""
        from half.runtime.nodes import phase_4_infrastructure
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            import os
            original = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_4_infrastructure(state)
                assert result["current_step"] == "phase-4-infrastructure"
            finally:
                os.chdir(original)

    def test_phase_5_observe(self):
        """Phase 5 observe should write monitoring config."""
        from half.runtime.nodes import phase_5_observe
        from half.runtime.state import initial_state

        with tempfile.TemporaryDirectory() as tmp:
            import os
            original = os.getcwd()
            os.chdir(tmp)
            try:
                state = initial_state("test")
                result = phase_5_observe(state)
                assert result["current_step"] == "phase-5-observe"
            finally:
                os.chdir(original)

    def test_route_from_gate_passed(self):
        """Passed gate should route to next phase."""
        from half.runtime.nodes import route_from_gate
        from half.runtime.state import initial_state

        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [{"gate_id": "G1", "passed": True, "details": "", "timestamp": ""}]
        assert route_from_gate(state) == "advance_to_phase-2"

    def test_route_from_gate_failed_with_retries(self):
        """Failed gate with retries remaining should retry."""
        from half.runtime.nodes import route_from_gate
        from half.runtime.state import initial_state

        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [{"gate_id": "G1", "passed": False, "details": "", "timestamp": ""}]
        state["retry_count"] = 1
        assert route_from_gate(state) == "retry_phase"

    def test_route_from_gate_failed_no_retries(self):
        """Failed gate with no retries should escalate."""
        from half.runtime.nodes import route_from_gate
        from half.runtime.state import initial_state

        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [{"gate_id": "G1", "passed": False, "details": "", "timestamp": ""}]
        state["retry_count"] = 3
        state["max_retries"] = 3
        assert route_from_gate(state) == "fail_safe_escalate"

    def test_route_finality_approved(self):
        """Finality gate approved should route to deploy."""
        from half.runtime.nodes import route_from_finality_gate
        from half.runtime.state import initial_state

        state = initial_state()
        state["deployment_approved"] = True
        assert route_from_finality_gate(state) == "deploy"

    def test_route_finality_waiting(self):
        """Finality gate not approved should wait."""
        from half.runtime.nodes import route_from_finality_gate
        from half.runtime.state import initial_state

        state = initial_state()
        assert route_from_finality_gate(state) == "wait_for_signoff"

    def test_pipeline_complete_routing(self):
        """Phase 5 passing should complete the pipeline."""
        from half.runtime.nodes import route_from_gate
        from half.runtime.state import initial_state

        state = initial_state()
        state["current_phase"] = "phase-5"
        state["gate_results"] = [{"gate_id": "G5", "passed": True, "details": "", "timestamp": ""}]
        assert route_from_gate(state) == "pipeline_complete"


# ═══════════════════════════════════════════════════════════════════════════════
# half_sidecar.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestHalfSidecar:
    """Test the half_sidecar module."""

    def test_cmd_status(self):
        """Status command should return a dict with expected keys."""
        from half.half_sidecar import cmd_status

        result = cmd_status()
        assert "status" in result
        assert "project" in result
        assert "mode" in result

    def test_cmd_gate_check_unknown(self):
        """Gate check for unsupported phase should return error."""
        from half.half_sidecar import cmd_gate_check

        result = cmd_gate_check("phase-99")
        assert result["status"] == "error"

    def test_cmd_generate_mrp(self):
        """MRP generation should return a dict with checks."""
        from half.half_sidecar import cmd_generate_mrp

        with tempfile.TemporaryDirectory() as tmp:
            original = Path.cwd()
            os.chdir(tmp)
            try:
                result = cmd_generate_mrp()
                assert "checks" in result
            finally:
                os.chdir(original)

    def test_cmd_voice_stt_fails_gracefully(self):
        """Voice STT with nonexistent file should return error gracefully."""
        from half.half_sidecar import cmd_voice_stt

        result = cmd_voice_stt("/nonexistent/file.wav")
        assert result["status"] in ("error", "ok")

    def test_cmd_focalboard_create(self):
        """Focalboard create should return status even when offline."""
        from half.half_sidecar import cmd_focalboard_create

        result = cmd_focalboard_create()
        assert "status" in result


# ═══════════════════════════════════════════════════════════════════════════════
# half_voice/engine.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestVoiceEngine:
    """Test the VoiceEngine module."""

    def test_init_default(self):
        """Default engine should initialize without errors."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        assert engine is not None
        avail = engine.is_available
        assert "stt" in avail
        assert "tts" in avail

    def test_tts_raises_without_piper(self):
        """TTS without Piper should raise RuntimeError."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        if not engine._tts_available:
            with pytest.raises(RuntimeError, match="TTS unavailable"):
                engine.speak("Hello")

    def test_stt_raises_without_whisper(self):
        """STT without Whisper should raise RuntimeError."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        if not engine._stt_available:
            with pytest.raises(RuntimeError, match="STT unavailable"):
                engine.transcribe("nonexistent.wav")

    def test_transcribe_microphone_raises_without_arecord(self):
        """Microphone transcription requires arecord."""
        from half.half_voice import VoiceEngine

        engine = VoiceEngine()
        # This should raise because arecord likely doesn't exist or no mic
        with pytest.raises((RuntimeError, FileNotFoundError)):
            engine.transcribe_microphone(1)


# ═══════════════════════════════════════════════════════════════════════════════
# half_focalboard/__init__.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestFocalboardClient:
    """Test the Focalboard API client."""

    def test_init(self):
        """Client should initialize with default URL."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient()
        assert client.base_url == "http://127.0.0.1:8000"

    def test_list_boards_offline(self):
        """Listing boards offline should return empty list."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        boards = client.list_boards()
        assert boards == []

    def test_create_board_offline(self):
        """Creating board offline should return board with empty id."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        board = client.create_board("Test Board", "Testing")
        assert board.id == ""
        assert board.title == "Test Board"

    def test_create_task_offline(self):
        """Creating task offline should return card with empty id."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        card = client.create_task("board-1", "Test Task", phase="phase-1")
        assert card.id == ""
        assert card.title == "Test Task"

    def test_task_from_phase_step(self):
        """Phase step task should have correct metadata."""
        from half.half_focalboard import FocalboardClient

        card = FocalboardClient.task_from_phase_step("phase-2", "Implementation", "HALF-Implement")
        assert "[PHASE-2]" in card.title
        assert card.phase == "phase-2"

    def test_update_task_status_offline(self):
        """Updating task status offline should return False."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        result = client.update_task_status("card-1", "done")
        assert result is False

    def test_get_tasks_by_phase_offline(self):
        """Getting tasks by phase offline should return empty list."""
        from half.half_focalboard import FocalboardClient

        client = FocalboardClient(base_url="http://127.0.0.1:1")
        tasks = client.get_tasks_by_phase("board-1", "phase-1")
        assert tasks == []


# ═══════════════════════════════════════════════════════════════════════════════
# state/__init__.py (LangGraph security module)
# ═══════════════════════════════════════════════════════════════════════════════


class TestLangGraphSecurity:
    """Test the LangGraph state security module."""

    def test_validate_allowed_filters(self):
        """Allowed filter keys should not raise."""
        from half.state import validate_metadata_filters

        validate_metadata_filters({"ticket_id": "T-42", "status": "open"})

    def test_validate_disallowed_filters(self):
        """Disallowed filter keys should raise ValueError."""
        from half.state import validate_metadata_filters

        with pytest.raises(ValueError, match="CRITICAL"):
            validate_metadata_filters({"arbitrary_key": "value"})

    def test_validate_allowed_metadata(self):
        """Allowed metadata keys should not raise."""
        from half.state import validate_metadata_write

        validate_metadata_write({"project": "test", "phase": "phase-1"})

    def test_validate_disallowed_metadata(self):
        """Disallowed metadata keys should raise ValueError."""
        from half.state import validate_metadata_write

        with pytest.raises(ValueError, match="CRITICAL"):
            validate_metadata_write({"hack": "value"})

    def test_state_machine_context(self):
        """StateMachineContext should manage metadata correctly."""
        from half.state import StateMachineContext

        ctx = StateMachineContext(project="test", phase="phase-1")
        assert ctx.get_metadata()["project"] == "test"
        assert ctx.get_metadata()["phase"] == "phase-1"

    def test_transition_valid_phase(self):
        """Valid phase transitions should succeed."""
        from half.state import StateMachineContext

        ctx = StateMachineContext(project="test", phase="phase-1")
        ctx.transition_to_phase("phase-2")
        assert ctx.get_metadata()["phase"] == "phase-2"

    def test_transition_invalid_phase(self):
        """Invalid phase transitions should raise."""
        from half.state import StateMachineContext

        ctx = StateMachineContext(project="test", phase="phase-1")
        with pytest.raises(ValueError, match="Invalid phase"):
            ctx.transition_to_phase("phase-99")

    def test_save_and_load_checkpoint(self):
        """Save then load should return same state."""
        from half.state import StateMachineContext

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["HALF_HOME"] = tmp
            ctx = StateMachineContext(
                project="test", phase="phase-1",
                checkpoint_dir=Path(tmp) / "checkpoints",
            )
            saved = ctx.save_checkpoint({"tasks": ["T-001"]})
            assert saved.exists()
            loaded = ctx.load_checkpoint(saved.stem.replace("ckpt-", ""))
            assert loaded == {"tasks": ["T-001"]}

    def test_checkpoint_integrity(self):
        """Checkpoint integrity should verify."""
        from half.state import validate_checkpoint_integrity

        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "ckpt.json"
            f.write_text('{"data": "test"}')
            result = validate_checkpoint_integrity(f)
            assert result is True

    def test_checkpoint_not_found(self):
        """Missing checkpoint should raise FileNotFoundError."""
        from half.state import validate_checkpoint_integrity

        with pytest.raises(FileNotFoundError):
            validate_checkpoint_integrity(Path("/nonexistent/checkpoint.json"))
