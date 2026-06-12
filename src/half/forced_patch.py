"""HALF 1.5 — Forced Patching Loop.

When test exit code is non-zero, captures stderr and pipes it directly
back into the model's context window, activating the Self-Correction Loop
until the code mathematically compiles.

Based on the HALF 1.5 doctrine's 'Forced Patching' specification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from half.sandbox_exec import SandboxExecutor, SandboxResult
from half.self_correct import SelfCorrectionLoop

logger = logging.getLogger("half.forced_patch")


@dataclass
class PatchAttempt:
    """A single forced patching attempt."""

    attempt: int
    command: str
    stderr: str
    passed: bool
    correction_actions: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""


@dataclass
class PatchCycleResult:
    """Result of a forced patching cycle."""

    success: bool = False
    total_attempts: int = 0
    max_attempts: int = 5
    attempts: list[PatchAttempt] = field(default_factory=list)
    final_stderr: str = ""
    summary: str = ""


class ForcedPatchingLoop:
    """Captures test stderr and forces the agent to patch until code compiles.

    Cycle:
    1. Run tests in sandbox
    2. If exit code != 0, capture stderr
    3. Pipe stderr + context into Self-Correction Loop
    4. Self-Correction pinpoints failure lines and generates fixes
    5. Apply fixes and retry
    6. Repeat until tests pass or max attempts reached
    """

    def __init__(self, max_attempts: int = 5):
        self.max_attempts = max_attempts
        self.sandbox = SandboxExecutor()
        self.corrector = SelfCorrectionLoop()

    def run_cycle(self, commands: list[str] | None = None) -> PatchCycleResult:
        """Execute a full forced patching cycle.

        Args:
            commands: Test commands to run. Defaults to full suite.

        Returns:
            PatchCycleResult with all attempts and final status.
        """
        result = PatchCycleResult(max_attempts=self.max_attempts)

        for attempt in range(1, self.max_attempts + 1):
            logger.info("Forced Patch: Attempt %d/%d", attempt, self.max_attempts)

            # Step 1: Run tests in sandbox
            if commands:
                for cmd in commands:
                    sandbox_result = self.sandbox.run_tests(cmd)
            else:
                sandbox_result = self.sandbox.run_full_test_suite()

            # Step 2: Analyze failure
            stderr = self.sandbox.get_stderr_for_patching(sandbox_result)

            attempt_record = PatchAttempt(
                attempt=attempt,
                command="; ".join(sandbox_result.commands_run),
                stderr=stderr,
                passed=sandbox_result.passed,
                created_at=datetime.now(tz=UTC).isoformat(),
            )

            # Step 3: If passed, we're done
            if sandbox_result.passed:
                result.success = True
                result.total_attempts = attempt
                result.attempts.append(attempt_record)
                result.summary = f"All tests passed after {attempt} attempt(s)"
                logger.info(result.summary)
                return result

            # Step 4: Analyze stderr and generate corrections
            correction_report = self.corrector.analyze_failure(
                stderr=sandbox_result.stderr,
                stdout=sandbox_result.stdout,
            )

            attempt_record.correction_actions = [
                {
                    "type": a.action_type,
                    "file": a.target_file,
                    "line": a.target_line,
                    "guidance": a.guidance,
                }
                for a in correction_report.actions
            ]

            result.attempts.append(attempt_record)

            if attempt < self.max_attempts:
                logger.info(
                    "Forced Patch: Attempt %d failed — %d corrective actions generated. Retrying...",
                    attempt,
                    len(correction_report.actions),
                )

        # Max attempts reached without success
        result.success = False
        result.total_attempts = self.max_attempts
        result.final_stderr = result.attempts[-1].stderr if result.attempts else ""
        result.summary = f"Forced patching failed after {self.max_attempts} attempts"
        logger.warning(result.summary)
        return result

    def generate_patch_prompt(self, result: SandboxResult) -> str:
        """Generate a system prompt that forces the agent to fix the errors.

        Args:
            result: SandboxResult from failed test run.

        Returns:
            Prompt text to inject into model context.
        """
        stderr = self.sandbox.get_stderr_for_patching(result)
        return (
            "[FORCED PATCHING MODE]\n"
            "The test suite failed with the following errors:\n"
            f"```\n{stderr}\n```\n"
            "You MUST fix ALL errors before proceeding. Do NOT ask for help.\n"
            "Analyze each error, determine the root cause, apply the fix, "
            "and re-run the tests. Repeat until the full suite passes.\n"
            "Do NOT escalate to the human operator.\n"
            "[/FORCED PATCHING MODE]"
        )
