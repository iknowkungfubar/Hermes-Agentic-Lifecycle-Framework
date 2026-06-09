"""Tests for HALF LangGraph runtime."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.runtime.checkpointer import create_secure_checkpointer, get_checkpoint_paths
from src.runtime.state import HalfState, initial_state, is_gate_passed
from src.runtime.nodes import route_from_gate, route_from_finality_gate


class TestInitialState:
    """Test initial state creation."""

    def test_default_state(self):
        """Default initial state should have expected values."""
        state = initial_state()
        assert state["project_name"] == "default"
        assert state["mode"] == "full"
        assert state["current_phase"] == "phase-1"
        assert state["current_step"] == "start"
        assert state["error_budget_remaining"] == 100
        assert state["retry_count"] == 0
        assert state["escalation_level"] == 0
        assert state["deployment_approved"] is False

    def test_custom_state(self):
        """Custom initial state should use provided values."""
        state = initial_state(project_name="my-app", mode="prototype")
        assert state["project_name"] == "my-app"
        assert state["mode"] == "prototype"


class TestGateResults:
    """Test gate result utilities."""

    def test_is_gate_passed_true(self):
        """Should return True for a passed gate."""
        state = initial_state()
        state["gate_results"] = [
            {"gate_id": "G1", "passed": True, "details": "ok", "timestamp": ""}
        ]
        assert is_gate_passed(state, "G1") is True

    def test_is_gate_passed_false(self):
        """Should return False for a failed gate."""
        state = initial_state()
        state["gate_results"] = [
            {"gate_id": "G1", "passed": False, "details": "fail", "timestamp": ""}
        ]
        assert is_gate_passed(state, "G1") is False

    def test_is_gate_passed_no_results(self):
        """Should return False when no gate results exist."""
        state = initial_state()
        assert is_gate_passed(state, "G1") is False


class TestRouteFromGate:
    """Test gate routing logic."""

    def test_passed_gate_routes_to_next_phase(self):
        """A passed gate should route to the next phase."""
        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [
            {"gate_id": "G1", "passed": True, "details": "ok", "timestamp": ""}
        ]
        result = route_from_gate(state)
        assert result == "advance_to_phase-2"

    def test_passed_phase2_routes_to_phase3(self):
        """Phase 2 gate passes → route to Phase 3."""
        state = initial_state()
        state["current_phase"] = "phase-2"
        state["gate_results"] = [
            {"gate_id": "G2", "passed": True, "details": "ok", "timestamp": ""}
        ]
        result = route_from_gate(state)
        assert result == "advance_to_phase-3"

    def test_passed_phase5_routes_to_complete(self):
        """Phase 5 gate passes → pipeline complete."""
        state = initial_state()
        state["current_phase"] = "phase-5"
        state["gate_results"] = [
            {"gate_id": "G5", "passed": True, "details": "ok", "timestamp": ""}
        ]
        result = route_from_gate(state)
        assert result == "pipeline_complete"

    def test_failed_gate_with_retries_remaining(self):
        """Failed gate with retries left → retry."""
        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [
            {"gate_id": "G1", "passed": False, "details": "fail", "timestamp": ""}
        ]
        state["retry_count"] = 1
        state["max_retries"] = 3
        result = route_from_gate(state)
        assert result == "retry_phase"

    def test_failed_gate_no_retries_remaining(self):
        """Failed gate with no retries left → escalate."""
        state = initial_state()
        state["current_phase"] = "phase-1"
        state["gate_results"] = [
            {"gate_id": "G1", "passed": False, "details": "fail", "timestamp": ""}
        ]
        state["retry_count"] = 3
        state["max_retries"] = 3
        result = route_from_gate(state)
        assert result == "fail_safe_escalate"


class TestRouteFromFinalityGate:
    """Test Finality Gate routing."""

    def test_approved_routes_to_deploy(self):
        """Approved deployment → deploy."""
        state = initial_state()
        state["deployment_approved"] = True
        assert route_from_finality_gate(state) == "deploy"

    def test_not_approved_routes_to_wait(self):
        """Not approved → wait for signoff."""
        state = initial_state()
        state["deployment_approved"] = False
        assert route_from_finality_gate(state) == "wait_for_signoff"


class TestCheckpointer:
    """Test secure checkpointer creation."""

    def test_create_checkpointer(self):
        """Creating a checkpointer should initialize DB with WAL."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "checkpoints.db")
            cp = create_secure_checkpointer(db_path)
            assert cp is not None
            assert Path(db_path).exists()

    def test_checkpoint_paths(self):
        """Checkpoint paths should include db, wal, shm."""
        with tempfile.TemporaryDirectory() as tmp:
            paths = get_checkpoint_paths(tmp)
            assert "db" in paths
            assert "wal" in paths
            assert "shm" in paths
            assert str(paths["db"]).endswith("checkpoints.db")
