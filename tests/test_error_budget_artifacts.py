"""Tests for error_budget.py and artifacts.py — pushing coverage to 100%."""

from __future__ import annotations

import tempfile
from datetime import UTC
from pathlib import Path

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# error_budget.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorBudgetTracker:
    """Test the ErrorBudgetTracker class (0% → 100% target)."""

    def test_create_with_defaults(self):
        """Default budget should be 100 points, healthy level."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            status = budget.get_status()
            assert status["total"] == 100
            assert status["remaining"] == 100
            assert status["percentage"] == 100.0
            assert status["level"] == "healthy"
            assert status["events_in_window"] == 0

    def test_create_custom_points(self):
        """Custom total points should be respected."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=500, state_dir=Path(tmp))
            status = budget.get_status()
            assert status["total"] == 500
            assert status["remaining"] == 500

    def test_record_failure_deducts_points(self):
        """Recording a failure should deduct the correct amount."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            budget.record_failure("phase_1_gate_fail", "Test failure")
            status = budget.get_status()
            assert status["remaining"] == 95  # 100 - 5
            assert status["level"] == "healthy"

    def test_multiple_failures_deduct_accumulatively(self):
        """Multiple failures should deduct points accumulatively."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            budget.record_failure("phase_1_gate_fail")  # -5
            budget.record_failure("phase_2_gate_fail")  # -10
            budget.record_failure("phase_3_gate_fail")  # -15
            status = budget.get_status()
            assert status["remaining"] == 70  # 100 - 5 - 10 - 15

    def test_all_deduction_types(self):
        """All known deduction types should work."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            deductions = {
                "phase_1_gate_fail": 5,
                "phase_2_gate_fail": 10,
                "phase_3_gate_fail": 15,
                "phase_4_gate_fail": 20,
                "production_incident_p1": 25,
                "production_incident_p2": 15,
                "production_incident_p3": 5,
            }
            total_deducted = sum(deductions.values())
            for event_type in deductions:
                budget.record_failure(event_type)
            status = budget.get_status()
            assert status["remaining"] == 100 - total_deducted

    def test_exhaust_budget(self):
        """Exhausting the budget should show exhausted level."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=20, state_dir=Path(tmp))
            budget.record_failure("production_incident_p1")  # -25
            status = budget.get_status()
            assert status["remaining"] == 0
            assert status["level"] == "exhausted"

    def test_warning_threshold(self):
        """Budget below 40% should show warning level."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            # Deduct 65 points (35 remaining = 35%) → warning (<40)
            for _ in range(4):
                budget.record_failure("phase_2_gate_fail")  # -10 each
            budget.record_failure("phase_3_gate_fail")  # -15
            budget.record_failure("phase_4_gate_fail")  # -20
            # Total: -75, remaining: 25, percentage: 25% → warning
            status = budget.get_status()
            assert status["percentage"] < 40
            assert status["level"] in ("warning", "critical")

    def test_critical_threshold(self):
        """Budget below 20% should show critical level."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            # Deduct 90 points → 10% → critical
            budget.record_failure("production_incident_p1")  # -25
            budget.record_failure("production_incident_p1")  # -25
            budget.record_failure("production_incident_p1")  # -25
            budget.record_failure("phase_4_gate_fail")  # -20
            status = budget.get_status()
            assert status["percentage"] < 20
            assert status["level"] == "critical"

    def test_invalid_event_type_raises(self):
        """Invalid event type should raise ValueError."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            with pytest.raises(ValueError, match="Unknown event type"):
                budget.record_failure("nonexistent_type")

    def test_get_events_filtered_by_type(self):
        """Getting events filtered by type should work."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            budget.record_failure("phase_1_gate_fail")
            budget.record_failure("production_incident_p1")
            budget.record_failure("phase_2_gate_fail")
            events = budget.get_events(event_type="phase_1_gate_fail")
            assert len(events) >= 1
            assert events[0]["event_type"] == "phase_1_gate_fail"

    def test_save_and_load_persists(self):
        """Events should persist across instances via JSON file."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget1 = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            budget1.record_failure("phase_1_gate_fail")
            budget1.record_failure("phase_2_gate_fail")

            # Create new instance pointing to same dir
            budget2 = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            status = budget2.get_status()
            assert status["remaining"] == 85  # 100 - 5 - 10

    def test_reset_clears_events(self):
        """Reset should clear all events."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            budget.record_failure("phase_1_gate_fail")
            budget.reset()
            status = budget.get_status()
            assert status["remaining"] == 100
            assert len(budget.get_events()) == 0

    def test_prune_old_events(self):
        """Events outside the window should be pruned."""
        from datetime import datetime, timedelta

        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(
                total_points=100, window_days=30, state_dir=Path(tmp)
            )
            # Manually add an old event
            old_time = (datetime.now(tz=UTC) - timedelta(days=60)).isoformat()
            budget._events.append(
                {
                    "event_type": "phase_1_gate_fail",
                    "deduction": 5,
                    "timestamp": old_time,
                    "details": "old event",
                }
            )
            budget._prune_old_events()
            assert len(budget._events) == 0  # Should have been pruned

    def test_calculate_remaining_stays_non_negative(self):
        """Remaining should never go below 0."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=10, state_dir=Path(tmp))
            budget.record_failure("production_incident_p1")  # -25
            budget.record_failure("production_incident_p1")  # -25
            status = budget.get_status()
            assert status["remaining"] == 0  # Not negative

    def test_get_status_with_empty_events(self):
        """Status with no events should show full budget."""
        from half.core.error_budget import ErrorBudgetTracker

        with tempfile.TemporaryDirectory() as tmp:
            budget = ErrorBudgetTracker(total_points=100, state_dir=Path(tmp))
            status = budget.get_status()
            assert status["events_in_window"] == 0
            assert status["remaining"] == 100
            assert status["level"] == "healthy"


# ═══════════════════════════════════════════════════════════════════════════════
# artifacts.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestArtifactManager:
    """Test the ArtifactManager class (0% → 100% target)."""

    def test_create_manager(self):
        """Creating a manager should create the base directory."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp) / "artifacts")
            assert mgr.base_dir.exists()

    def test_ensure_phase_dir(self):
        """Ensuring a phase directory should create it."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            phase_dir = mgr.ensure_phase_dir("phase-1")
            assert phase_dir.exists()
            assert phase_dir.name == "phase-1"

    def test_write_artifact(self):
        """Writing an artifact should create the file."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            path = mgr.write_artifact("phase-1", "test.md", "# Hello World")
            assert path.exists()
            assert path.read_text() == "# Hello World"

    def test_read_artifact(self):
        """Reading an artifact should return its content."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            mgr.write_artifact("phase-1", "test.md", "# Content")
            content = mgr.read_artifact("phase-1", "test.md")
            assert content == "# Content"

    def test_read_nonexistent_artifact(self):
        """Reading a nonexistent artifact should return None."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            content = mgr.read_artifact("phase-1", "nonexistent.md")
            assert content is None

    def test_verify_phase_artifacts_all_present(self):
        """Verifying phase artifacts should return all True when present."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            for name in ["01-REQUIREMENTS.md", "02-SPECIFICATION.md"]:
                mgr.write_artifact("phase-1", name, "# content")
            results = mgr.verify_phase_artifacts("phase-1")
            assert results["01-REQUIREMENTS.md"] is True
            assert results["02-SPECIFICATION.md"] is True

    def test_verify_phase_artifacts_missing(self):
        """Verifying phase artifacts should return False for missing."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            results = mgr.verify_phase_artifacts("phase-1")
            assert results["01-REQUIREMENTS.md"] is False

    def test_all_phases_complete(self):
        """All phases complete should check all phases."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            # By default, nothing exists
            results = mgr.all_phases_complete()
            assert results["phase-1"] is False

    def test_list_artifacts_no_filter(self):
        """Listing artifacts without filter should return all."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            mgr.write_artifact("phase-1", "a.md", "a")
            mgr.write_artifact("phase-2", "b.md", "b")
            all_artifacts = mgr.list_artifacts()
            assert len(all_artifacts) >= 2

    def test_list_artifacts_filtered(self):
        """Listing artifacts with phase filter should return only that phase."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            mgr.write_artifact("phase-1", "a.md", "a")
            mgr.write_artifact("phase-2", "b.md", "b")
            phase1 = mgr.list_artifacts("phase-1")
            assert len(phase1) == 1
            assert "a.md" in phase1[0].name

    def test_list_artifacts_nonexistent_phase(self):
        """Listing artifacts for a nonexistent phase should return empty list."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            result = mgr.list_artifacts("phase-99")
            assert result == []

    def test_get_phase_summary(self):
        """Getting phase summary should return artifact details."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            mgr.write_artifact("phase-1", "test.md", "# Hello\n\nWorld")
            summary = mgr.get_phase_summary("phase-1")
            assert summary["exists"] is True
            assert summary["artifact_count"] >= 1
            assert len(summary["artifacts"]) >= 1
            assert summary["artifacts"][0]["name"] == "test.md"
            assert summary["artifacts"][0]["size"] > 0

    def test_get_phase_summary_nonexistent(self):
        """Getting summary for a nonexistent phase should return not exists."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            summary = mgr.get_phase_summary("phase-99")
            assert summary["exists"] is False

    def test_write_then_read_roundtrip(self):
        """Write then read should return identical content."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            original = "# Complex Document\n\nWith multiple paragraphs\n\n- List item 1\n- List item 2\n"
            mgr.write_artifact("phase-1", "doc.md", original)
            roundtrip = mgr.read_artifact("phase-1", "doc.md")
            assert roundtrip == original

    def test_phase_2_has_empty_required(self):
        """Phase 2 should have no required artifacts (empty list)."""
        from half.core.artifacts import ArtifactManager

        required = ArtifactManager.REQUIRED_ARTIFACTS.get("phase-2", [])
        assert required == []

    def test_phase_3_required_artifacts(self):
        """Phase 3 should have required artifacts defined."""
        from half.core.artifacts import ArtifactManager

        required = ArtifactManager.REQUIRED_ARTIFACTS.get("phase-3", [])
        assert len(required) >= 3
        assert "security-scan.md" in required

    def test_verify_all_phases(self):
        """Verify all phases should return dict with all 5 phases."""
        from half.core.artifacts import ArtifactManager

        with tempfile.TemporaryDirectory() as tmp:
            mgr = ArtifactManager(Path(tmp))
            results = mgr.all_phases_complete()
            assert "phase-1" in results
            assert "phase-2" in results
            assert "phase-3" in results
            assert "phase-4" in results
            assert "phase-5" in results
