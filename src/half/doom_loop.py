"""HALF — Doom Loop Mitigation.

If an agent gets stuck in a retry cycle filling its context window with
tracebacks, this module forcefully truncates the conversation history upon
reaching the retry limit, summarizes the failure, and starts a fresh session
with only the initial spec.

Based on the HALF doctrine's 'Doom Loop Mitigation' specification.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.doom_loop")


@dataclass
class RetryRecord:
    """Record of a single retry attempt."""

    attempt: int
    timestamp: str
    error_type: str  # test_failure, compile_error, timeout, crash
    error_summary: str  # First 200 chars of the error
    traceback_length: int


@dataclass
class SessionState:
    """State of a session that might be in a doom loop."""

    session_id: str
    initial_spec: str  # The original prompt/spec
    retries: list[RetryRecord] = field(default_factory=list)
    truncated: bool = False
    recovery_summary: str = ""


class DoomLoopDetector:
    """Detects and mitigates doom loops (infinite retry cycles).

    Monitors retry attempts and detects patterns indicating a doom loop:
    - Consecutive failures with the same error type
    - Growing traceback length (context window filling with noise)
    - No progress on the success metric across attempts

    When detected, truncates history and restarts with only the initial spec.
    """

    def __init__(
        self,
        max_retries: int = 5,
        max_traceback_chars: int = 5000,
        state_dir: str | Path = ".hale/state/sessions",
    ):
        self.max_retries = max_retries
        self.max_traceback_chars = max_traceback_chars
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionState] = {}

    def register_session(self, session_id: str, initial_spec: str) -> SessionState:
        """Register a new session for doom loop monitoring.

        Args:
            session_id: Unique session identifier.
            initial_spec: The original prompt/spec to fall back to on truncation.

        Returns:
            The new SessionState.
        """
        state = SessionState(
            session_id=session_id,
            initial_spec=initial_spec,
        )
        self._sessions[session_id] = state
        self._save_state(state)
        logger.info("Doom Loop Monitor: Registered session %s", session_id)
        return state

    def record_retry(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        traceback_text: str,
    ) -> dict[str, Any]:
        """Record a retry attempt and check for doom loop.

        Args:
            session_id: Session identifier.
            error_type: Type of error (test_failure, compile_error, timeout, crash).
            error_message: The error message or summary.
            traceback_text: Full traceback text.

        Returns:
            Dict with {
                'doom_loop_detected': bool,
                'truncated': bool,
                'recovery_summary': str,
                'retry_count': int,
            }
        """
        state = self._sessions.get(session_id)
        if not state:
            return {
                "doom_loop_detected": False,
                "truncated": False,
                "recovery_summary": "Session not found",
                "retry_count": 0,
            }

        record = RetryRecord(
            attempt=len(state.retries) + 1,
            timestamp=datetime.now(tz=UTC).isoformat(),
            error_type=error_type,
            error_summary=error_message[:200],
            traceback_length=len(traceback_text),
        )
        state.retries.append(record)
        self._save_state(state)

        # Check for doom loop conditions
        result = self._analyze(state)

        if result["doom_loop_detected"]:
            logger.warning(
                "Doom Loop DETECTED in session %s after %d retries. Truncating.",
                session_id,
                len(state.retries),
            )
            recovery = self._truncate(state)
            result["truncated"] = True
            result["recovery_summary"] = recovery

        return result

    def _analyze(self, state: SessionState) -> dict[str, Any]:
        """Analyze retry history for doom loop patterns.

        Returns:
            Dict with doom_loop_detected and reason.
        """
        retries = state.retries
        if len(retries) < 3:
            return {"doom_loop_detected": False, "reason": "Not enough retries yet"}

        # Condition 1: Max retries exceeded
        if len(retries) >= self.max_retries:
            return {
                "doom_loop_detected": True,
                "reason": f"Exceeded max retries ({self.max_retries})",
            }

        # Condition 2: Same error type 3+ times in a row
        recent = retries[-3:]
        if len({r.error_type for r in recent}) == 1:
            return {
                "doom_loop_detected": True,
                "reason": f"Same error type '{recent[0].error_type}' repeated {len(recent)} times",
            }

        # Condition 3: Growing traceback (context filling with noise)
        if len(retries) >= 3:
            traceback_growth = [
                retries[i].traceback_length - retries[i - 1].traceback_length
                for i in range(1, len(retries))
            ]
            avg_growth = sum(traceback_growth) / len(traceback_growth)
            if avg_growth > 500:  # Growing by >500 chars per retry
                return {
                    "doom_loop_detected": True,
                    "reason": f"Traceback growing by {avg_growth:.0f} chars per retry (context pollution)",
                }

        return {"doom_loop_detected": False, "reason": "No doom loop detected"}

    def _truncate(self, state: SessionState) -> str:
        """Truncate the session — summarize failures and restart with initial spec.

        Args:
            state: The session state to truncate.

        Returns:
            A recovery summary string.
        """
        state.truncated = True

        # Build recovery summary
        error_counts: dict[str, int] = {}
        for r in state.retries:
            error_counts[r.error_type] = error_counts.get(r.error_type, 0) + 1

        summary_parts = [
            f"## Recovery Summary — Session {state.session_id[:8]}",
            "",
            f"**Previous attempts:** {len(state.retries)}",
            "**Error breakdown:**",
        ]
        for err_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            summary_parts.append(f"- {err_type}: {count} occurrence(s)")

        summary_parts.extend(
            [
                "",
                "**Root cause analysis:**",
                self._analyze_root_cause(state.retries),
                "",
                "**Restarting fresh with original spec:**",
                "```",
                state.initial_spec[:500],
                "```" if len(state.initial_spec) > 500 else "",
            ]
        )

        state.recovery_summary = "\n".join(summary_parts)
        logger.info(
            "Doom Loop: Session %s truncated — recovery summary generated",
            state.session_id,
        )
        return state.recovery_summary

    @staticmethod
    def _analyze_root_cause(retries: list[RetryRecord]) -> str:
        """Analyze retry history to determine root cause.

        Args:
            retries: The retry history.

        Returns:
            Root cause analysis text.
        """
        if not retries:
            return "No retry data available"

        # Most common error type
        error_types: dict[str, int] = {}
        for r in retries:
            error_types[r.error_type] = error_types.get(r.error_type, 0) + 1
        most_common = max(error_types, key=lambda k: error_types[k])

        # Check if traceback is growing
        if len(retries) >= 2:
            first_tb = retries[0].traceback_length
            last_tb = retries[-1].traceback_length
            last_tb > first_tb * 2

        issues = []
        if most_common == "test_failure":
            issues.append(
                "Tests are consistently failing — check test fixtures or implementation logic"
            )
        elif most_common == "compile_error":
            issues.append("Code is not compiling — check for syntax or import errors")
        elif most_common == "timeout":
            issues.append(
                "Operations are timing out — check for infinite loops or slow dependencies"
            )

        if len(retries) >= 3:
            similar_errors = len({r.error_summary[:80] for r in retries[-3:]}) == 1
            if similar_errors:
                issues.append(
                    "Same error repeating — the fix applied is not addressing the root cause"
                )

        return (
            " ".join(issues)
            if issues
            else "No clear pattern detected — manual review recommended"
        )

    def get_session(self, session_id: str) -> SessionState | None:
        """Get a session state.

        Args:
            session_id: Session identifier.

        Returns:
            SessionState if found.
        """
        return self._sessions.get(session_id)

    def _save_state(self, state: SessionState) -> None:
        """Persist session state to disk."""
        state_file = self.state_dir / f"{state.session_id}.json"
        data = {
            "session_id": state.session_id,
            "initial_spec": state.initial_spec[:200],
            "truncated": state.truncated,
            "recovery_summary": state.recovery_summary,
            "retry_count": len(state.retries),
            "last_retry": state.retries[-1].timestamp if state.retries else "",
        }
        state_file.write_text(json.dumps(data, indent=2))
