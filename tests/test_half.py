"""Tests for HALF state machine security module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.state import (
    StateMachineContext,
    validate_metadata_filters,
    validate_metadata_write,
)


class TestMetadataValidation:
    """Test metadata filter and write validation."""

    def test_allowed_filter_keys_pass(self):
        """Allowed filter keys should not raise."""
        validate_metadata_filters({"ticket_id": "T-42", "status": "open"})
        validate_metadata_filters({"agent_id": "a1", "priority": "P0"})
        validate_metadata_filters({"phase": "phase-1"})

    def test_disallowed_filter_key_raises(self):
        """Disallowed filter keys should raise ValueError."""
        with pytest.raises(ValueError, match="CRITICAL"):
            validate_metadata_filters({"user_input": "hack"})

    def test_allowed_metadata_write_pass(self):
        """Allowed metadata keys should not raise."""
        validate_metadata_write({"project": "demo", "phase": "phase-1"})
        validate_metadata_write({"gate_id": "G1.1", "retry_count": 3})

    def test_disallowed_metadata_write_raises(self):
        """Disallowed metadata keys should raise ValueError."""
        with pytest.raises(ValueError, match="CRITICAL"):
            validate_metadata_write({"arbitrary_key": "value"})


class TestStateMachineContext:
    """Test StateMachineContext operations."""

    def test_create_context(self):
        """Creating a context should set initial metadata."""
        ctx = StateMachineContext(project="test-proj", phase="phase-1")
        meta = ctx.get_metadata()
        assert meta["project"] == "test-proj"
        assert meta["phase"] == "phase-1"

    def test_update_metadata(self):
        """Updating metadata should be reflected."""
        ctx = StateMachineContext(project="p", phase="phase-1")
        ctx.update_metadata({"gate_id": "G1.1", "retry_count": 2})
        meta = ctx.get_metadata()
        assert meta["gate_id"] == "G1.1"
        assert meta["retry_count"] == 2

    def test_transition_to_valid_phase(self):
        """Transitioning to a valid phase should update phase."""
        ctx = StateMachineContext(project="p", phase="phase-1")
        ctx.transition_to_phase("phase-2")
        assert ctx.get_metadata()["phase"] == "phase-2"

    def test_transition_to_invalid_phase_raises(self):
        """Transitioning to an invalid phase should raise."""
        ctx = StateMachineContext(project="p", phase="phase-1")
        with pytest.raises(ValueError, match="Invalid phase"):
            ctx.transition_to_phase("phase-99")

    def test_save_and_load_checkpoint(self):
        """Save then load a checkpoint should return state."""
        with tempfile.TemporaryDirectory() as tmp:
            ctx = StateMachineContext(
                project="test",
                phase="phase-1",
                checkpoint_dir=Path(tmp),
            )
            saved_path = ctx.save_checkpoint({"tasks": ["T-001"]})
            assert saved_path.exists()

            # Load the checkpoint
            ckpt_id = saved_path.stem.replace("ckpt-", "")
            state = ctx.load_checkpoint(ckpt_id)
            assert state == {"tasks": ["T-001"]}


class TestOrchestrator:
    """Test orchestrator basic operations."""

    def test_create_orchestrator(self):
        """Creating an orchestrator with default mode."""
        from src.core.orchestrator import Orchestrator, PipelineMode

        orch = Orchestrator(project_name="test", mode=PipelineMode.FULL)
        assert orch.project_name == "test"

    def test_pipeline_status(self):
        """Pipeline status should report correct initial state."""
        from src.core.orchestrator import Orchestrator, PipelineMode

        orch = Orchestrator(project_name="test", mode=PipelineMode.FULL)
        status = orch.get_pipeline_status()
        assert status["project"] == "test"
        assert status["active_phase"] is None
        assert status["completed_phases"] == []


class TestErrorBudget:
    """Test error budget tracking."""

    def test_create_budget(self):
        """Creating a budget should show full points."""
        from src.core.error_budget import ErrorBudgetTracker

        budget = ErrorBudgetTracker(total_points=100)
        status = budget.get_status()
        assert status["total"] == 100
        assert status["remaining"] == 100
        assert status["level"] == "healthy"

    def test_deduct_points(self):
        """Recording failures should deduct points."""
        from src.core.error_budget import ErrorBudgetTracker

        budget = ErrorBudgetTracker(total_points=100)
        budget.record_failure("phase_1_gate_fail", "Test failure")
        status = budget.get_status()
        assert status["remaining"] == 95
        assert status["level"] == "healthy"

    def test_exhaust_budget(self):
        """Recording many failures should exhaust the budget."""
        from src.core.error_budget import ErrorBudgetTracker

        budget = ErrorBudgetTracker(total_points=100)
        for _ in range(5):
            budget.record_failure("production_incident_p1")
        status = budget.get_status()
        assert status["remaining"] == 0
        assert status["level"] == "exhausted"

    def test_invalid_event_type_raises(self):
        """Invalid event type should raise ValueError."""
        from src.core.error_budget import ErrorBudgetTracker

        budget = ErrorBudgetTracker(total_points=100)
        with pytest.raises(ValueError, match="Unknown event type"):
            budget.record_failure("invalid_type")


class TestArtifactManager:
    """Test artifact manager operations."""

    def test_ensure_phase_dir(self):
        """Should create phase directory."""
        from src.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            phase_dir = mgr.ensure_phase_dir("phase-1")
            assert phase_dir.exists()
            assert phase_dir.name == "phase-1"

    def test_write_and_read_artifact(self):
        """Should write and read an artifact."""
        from src.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            mgr.write_artifact("phase-1", "test.md", "# Hello")
            result = mgr.read_artifact("phase-1", "test.md")
            assert result == "# Hello"
