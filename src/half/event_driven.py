"""HALF 1.5 — Event-Driven Agency.

Agents operate proactively, triggered by cron schedules, CI/CD pipeline
failures, or Kanban ticket updates — not by waiting for human prompts.

Based on the HALF 1.5 doctrine's 'Relentless Proactivity' specification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("half.event_driven")


@dataclass
class EventTrigger:
    """Configuration for an event trigger."""

    name: str
    trigger_type: str  # cron, ci_failure, kanban_update, webhook, file_change
    condition: str  # e.g., "0 6 * * *", "build:failed", "ticket:in_progress"
    action: str  # Command or function to execute
    enabled: bool = True
    last_fired: str = ""
    cooldown_seconds: int = 300


@dataclass
class TriggeredAction:
    """Result of a triggered action."""

    trigger_name: str
    status: str  # started, completed, failed
    output: str = ""
    started_at: str = ""
    completed_at: str = ""


class EventDrivenAgency:
    """Manages event-driven agent execution.

    Agents register triggers and are activated automatically when
    conditions are met. Supports cron schedules, CI pipeline failures,
    Kanban ticket state changes, and webhook payloads.

    Usage:
        agency = EventDrivenAgency()
        agency.register_trigger(EventTrigger(
            name="nightly-audit",
            trigger_type="cron",
            condition="0 6 * * *",
            action="half ralph-loop"
        ))
        agency.poll()  # Check all triggers
    """

    def __init__(self) -> None:
        self.triggers: list[EventTrigger] = []
        self._history: list[TriggeredAction] = []

    def register_trigger(self, trigger: EventTrigger) -> None:
        """Register a new event trigger.

        Args:
            trigger: The trigger configuration.
        """
        self.triggers.append(trigger)
        logger.info("Event Agency: Registered trigger '%s' (%s)", trigger.name, trigger.trigger_type)

    def remove_trigger(self, name: str) -> bool:
        """Remove a trigger by name.

        Args:
            name: Trigger name.

        Returns:
            True if removed.
        """
        before = len(self.triggers)
        self.triggers = [t for t in self.triggers if t.name != name]
        return len(self.triggers) < before

    def poll(self) -> list[TriggeredAction]:
        """Poll all triggers and execute any whose conditions are met.

        Returns:
            List of actions that were triggered.
        """
        now = datetime.now(tz=timezone.utc)
        fired: list[TriggeredAction] = []

        for trigger in self.triggers:
            if not trigger.enabled:
                continue

            should_fire = False

            if trigger.trigger_type == "cron":
                should_fire = self._check_cron(trigger.condition, now)
            elif trigger.trigger_type == "ci_failure":
                should_fire = self._check_ci_failure(trigger.condition)
            elif trigger.trigger_type == "kanban_update":
                should_fire = self._check_kanban(trigger.condition)

            if should_fire:
                action = self._execute(trigger)
                fired.append(action)
                trigger.last_fired = now.isoformat()

        return fired

    def _check_cron(self, expression: str, now: datetime) -> bool:
        """Check if a cron expression matches the current time.

        Args:
            expression: Cron expression (e.g., "0 6 * * *").
            now: Current datetime.

        Returns:
            True if the cron should fire.
        """
        import croniter
        try:
            cron = croniter.croniter(expression, now)
            prev = cron.get_prev(datetime)
            return (now - prev).total_seconds() < 90  # type: ignore[no-any-return]
        except (ImportError, ValueError, KeyError):
            # Fallback: check if it's a simple hourly/daily pattern
            parts = expression.split()
            if len(parts) == 5:
                minute, hour = parts[0], parts[1]
                if minute == "*" or minute == str(now.minute):
                    if hour == "*" or hour == str(now.hour):
                        return True
            return False

    def _check_ci_failure(self, branch: str) -> bool:
        """Check if CI has failed on a specific branch."""
        import subprocess
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--branch", branch, "--json", "conclusion", "--limit", "1"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                import json
                runs = json.loads(result.stdout)
                return any(r.get("conclusion") == "failure" for r in runs)
        except Exception:
            pass
        return False

    def _check_kanban(self, condition: str) -> bool:
        """Check if a Kanban condition is met.

        Args:
            condition: e.g., "ticket:in_progress", "ticket:blocked"

        Returns:
            True if condition met.
        """
        # Placeholder — in production, would query Focalboard API
        return False

    def _execute(self, trigger: EventTrigger) -> TriggeredAction:
        """Execute a trigger's action.

        Args:
            trigger: The trigger to fire.

        Returns:
            TriggeredAction with status.
        """
        import subprocess
        now = datetime.now(tz=timezone.utc).isoformat()
        logger.info("Event Agency: Firing trigger '%s' → %s", trigger.name, trigger.action)

        action = TriggeredAction(
            trigger_name=trigger.name,
            status="started",
            started_at=now,
        )

        try:
            result = subprocess.run(
                trigger.action.split(),
                capture_output=True, text=True, timeout=300,
            )
            action.status = "completed" if result.returncode == 0 else "failed"
            action.output = (result.stdout + result.stderr)[:500]
        except subprocess.TimeoutExpired:
            action.status = "failed"
            action.output = "Timed out after 300s"
        except Exception as e:
            action.status = "failed"
            action.output = str(e)

        action.completed_at = datetime.now(tz=timezone.utc).isoformat()
        self._history.append(action)
        return action

    def get_history(self, limit: int = 20) -> list[TriggeredAction]:
        """Get recent trigger execution history.

        Args:
            limit: Max entries to return.

        Returns:
            List of recent TriggeredActions.
        """
        return self._history[-limit:]

    def handle_ci_webhook(self, event: dict[str, Any]) -> list[TriggeredAction]:
        """Handle an incoming CI webhook event.

        Args:
            event: Webhook payload dict. Should contain 'status' and 'branch'.

        Returns:
            List of actions triggered by this event.
        """
        fired: list[TriggeredAction] = []
        status = event.get("status", "")
        branch = event.get("branch", "master")

        if status == "failure":
            for trigger in self.triggers:
                if trigger.trigger_type == "ci_failure" and trigger.condition == branch:
                    action = self._execute(trigger)
                    fired.append(action)
                    trigger.last_fired = datetime.now(tz=timezone.utc).isoformat()

        return fired
