"""
HALF — Error Budget Tracker

Tracks pipeline health via a point-based error budget.
Each gate failure or production incident deducts points.
When the budget is exhausted, automation pauses.
"""

from __future__ import annotations
from half import config

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.error_budget")


class ErrorBudgetTracker:
    """Track and manage the error budget for pipeline health.

    The budget is a point system: failures deduct points, and when
    the budget falls below thresholds, automation is restricted.
    """

    def __init__(
        self,
        total_points: int = 100,
        window_days: int = 30,
        state_dir: Path | None = None,
    ):
        self.total_points = total_points
        self.window_days = window_days
        self.state_dir = state_dir or Path(config.METRICS_DIR)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._events: list[dict[str, Any]] = []
        self._load()

    DEDUCTIONS = {
        "phase_1_gate_fail": 5,
        "phase_2_gate_fail": 10,
        "phase_3_gate_fail": 15,
        "phase_4_gate_fail": 20,
        "production_incident_p1": 25,
        "production_incident_p2": 15,
        "production_incident_p3": 5,
    }

    def record_failure(
        self,
        event_type: str,
        details: str = "",
    ) -> dict[str, Any]:
        """Record a failure event and deduct from budget.

        Args:
            event_type: Type of failure (must be in DEDUCTIONS).
            details: Optional description of the failure.

        Returns:
            Current budget state after deduction.

        Raises:
            ValueError: If event_type is not recognized.
        """
        if event_type not in self.DEDUCTIONS:
            msg = (
                f"Unknown event type: {event_type}. "
                f"Valid: {list(self.DEDUCTIONS.keys())}"
            )
            raise ValueError(msg)

        deduction = self.DEDUCTIONS[event_type]
        event = {
            "event_type": event_type,
            "deduction": deduction,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "details": details,
        }
        self._events.append(event)
        self._prune_old_events()
        self._save()

        remaining = self._calculate_remaining()
        logger.warning(
            "Error budget: -%d (%s). Remaining: %d/%d",
            deduction,
            event_type,
            remaining,
            self.total_points,
        )

        return self.get_status()

    def _prune_old_events(self) -> None:
        """Remove events outside the tracking window."""
        cutoff = datetime.now(tz=UTC) - timedelta(days=self.window_days)
        self._events = [
            e for e in self._events if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

    def _calculate_remaining(self) -> int:
        """Calculate remaining budget points."""
        total_deducted: int = sum(e["deduction"] for e in self._events)
        return max(0, self.total_points - total_deducted)

    def get_status(self) -> dict[str, Any]:
        """Get current error budget status.

        Returns:
            Dict with remaining points, percentage, and health level.
        """
        remaining = self._calculate_remaining()
        percentage = (remaining / self.total_points) * 100

        if percentage <= 0:
            level = "exhausted"
        elif percentage < 20:
            level = "critical"
        elif percentage < 40:
            level = "warning"
        else:
            level = "healthy"

        return {
            "total": self.total_points,
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "level": level,
            "events_in_window": len(self._events),
            "window_days": self.window_days,
        }

    def get_events(
        self,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get recent events, optionally filtered by type."""
        events = self._events
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-limit:]

    def _load(self) -> None:
        """Load events from state file."""
        state_file = self.state_dir / "error-budget.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                self._events = data.get("events", [])
                self._prune_old_events()
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to load error budget state, starting fresh")
                self._events = []

    def _save(self) -> None:
        """Save events to state file."""
        state_file = self.state_dir / "error-budget.json"
        state_file.write_text(json.dumps({"events": self._events}, indent=2))

    def reset(self) -> None:
        """Reset the error budget (clear all events)."""
        self._events = []
        self._save()
        logger.info("Error budget reset")
