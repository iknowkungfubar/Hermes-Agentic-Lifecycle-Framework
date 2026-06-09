"""
HALF — Fail-Safe Protocol Executor

Implements the 3-level escalation path:
1. Step retry (automatic, up to 3 attempts)
2. Phase retry (automatic with expanded context)
3. Human escalation (gap report generated, pipeline paused)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger("half.fail_safe")


class EscalationLevel(Enum):
    NONE = 0
    STEP_RETRY = 1
    PHASE_RETRY = 2
    HUMAN_ESCALATION = 3
    ABORT = 4


@dataclass
class FailSafeConfig:
    """Configuration for the fail-safe system."""

    enabled: bool = True
    max_step_retries: int = 3
    max_phase_retries: int = 2
    step_cooldown_seconds: int = 30
    log_path: Path = Path(".hale/logs/retries.log")


@dataclass
class EscalationState:
    """Tracks the current escalation state."""

    level: EscalationLevel = EscalationLevel.NONE
    step_retries: int = 0
    phase_retries: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)
    last_failure_time: float = 0.0


class FailSafeExecutor:
    """Executes the fail-safe protocol for phase execution.

    Wraps phase step execution with retry logic and escalation.
    """

    def __init__(self, config: FailSafeConfig | None = None):
        self.config = config or FailSafeConfig()
        self.state = EscalationState()

    def execute_with_retry(
        self,
        step_fn: Callable[[], tuple[bool, str]],
        step_name: str,
        gate_id: str,
    ) -> tuple[bool, dict[str, Any] | None]:
        """Execute a step with fail-safe retry logic.

        Args:
            step_fn: The step function to execute. Returns (success, details).
            step_name: Human-readable step name for logging.
            gate_id: The gate ID for this step.

        Returns:
            Tuple of (success, gap_report_data if escalated).
        """
        if not self.config.enabled:
            success, details = step_fn()
            return success, None

        self.state.level = EscalationLevel.STEP_RETRY

        for attempt in range(1, self.config.max_step_retries + 1):
            success, details = step_fn()
            self.state.last_failure_time = time.time()

            if success:
                self.state.level = EscalationLevel.NONE
                self.state.step_retries = 0
                logger.info("Step '%s' succeeded on attempt %d", step_name, attempt)
                return True, None

            logger.warning(
                "Step '%s' failed on attempt %d/%d: %s",
                step_name,
                attempt,
                self.config.max_step_retries,
                details,
            )
            self.state.failures.append(
                {
                    "attempt": attempt,
                    "gate_id": gate_id,
                    "step": step_name,
                    "details": details,
                    "timestamp": time.time(),
                }
            )
            self.state.step_retries += 1

            if attempt < self.config.max_step_retries:
                time.sleep(self.config.step_cooldown_seconds)

        # Step retries exhausted — escalate to phase retry
        logger.warning(
            "Step '%s' exhausted %d retries. Escalating to phase retry.",
            step_name,
            self.config.max_step_retries,
        )
        self.state.level = EscalationLevel.PHASE_RETRY

        return False, self._generate_gap_report(gate_id, step_name)

    def can_phase_retry(self) -> bool:
        """Check if phase-level retry is available."""
        return self.state.phase_retries < self.config.max_phase_retries

    def record_phase_retry(self) -> None:
        """Record a phase-level retry."""
        self.state.phase_retries += 1
        self.state.step_retries = 0
        self.state.level = EscalationLevel.PHASE_RETRY

    def escalate_to_human(self) -> None:
        """Escalate to human — pipeline pauses."""
        self.state.level = EscalationLevel.HUMAN_ESCALATION
        logger.critical(
            "Human escalation required. Pipeline paused. "
            "Generate gap report at .hale/gates/gap-report.md"
        )

    def _generate_gap_report(
        self,
        gate_id: str,
        step_name: str,
    ) -> dict[str, Any]:
        """Generate a structured gap report for human escalation."""
        return {
            "gate_id": gate_id,
            "step": step_name,
            "level": self.state.level.value,
            "failures": self.state.failures[-self.config.max_step_retries :],
            "retries_used": self.state.step_retries,
            "message": (
                f"Auto-remediation exhausted for gate {gate_id} on step '{step_name}'. "
                "Human intervention required."
            ),
        }

    def reset(self) -> None:
        """Reset fail-safe state for a new phase."""
        self.state = EscalationState()
        logger.info("Fail-safe state reset")
