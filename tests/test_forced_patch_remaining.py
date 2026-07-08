"""Target uncovered lines in forced_patch.py.

Covers dataclasses and generate_patch_prompt (lines 73-136 uncovered).
run_cycle needs mocking of SandboxExecutor and SelfCorrectionLoop.
"""

from __future__ import annotations


class TestPatchDataclasses:
    """Cover PatchAttempt and PatchCycleResult dataclasses."""

    def test_patch_attempt_defaults(self) -> None:
        """PatchAttempt with default values."""
        from half.forced_patch import PatchAttempt

        p = PatchAttempt(attempt=1, command="pytest", stderr="err", passed=False)
        assert p.attempt == 1
        assert p.correction_actions == []
        assert p.created_at == ""

    def test_patch_attempt_with_actions(self) -> None:
        """PatchAttempt with correction actions."""
        from half.forced_patch import PatchAttempt

        p = PatchAttempt(
            attempt=2,
            command="ruff check",
            stderr="lint error",
            passed=True,
            correction_actions=[{"type": "fix", "file": "test.py", "line": 10}],
            created_at="2026-01-01T00:00:00",
        )
        assert p.passed is True
        assert len(p.correction_actions) == 1
        assert p.correction_actions[0]["type"] == "fix"

    def test_patch_cycle_result_defaults(self) -> None:
        """PatchCycleResult with default values."""
        from half.forced_patch import PatchCycleResult

        r = PatchCycleResult()
        assert r.success is False
        assert r.total_attempts == 0
        assert r.max_attempts == 5
        assert r.attempts == []
        assert r.final_stderr == ""
        assert r.summary == ""

    def test_patch_cycle_result_with_attempts(self) -> None:
        """PatchCycleResult with attempts."""
        from half.forced_patch import PatchAttempt, PatchCycleResult

        r = PatchCycleResult()
        r.success = True
        r.total_attempts = 3
        r.attempts = [
            PatchAttempt(attempt=1, command="test", stderr="fail", passed=False),
            PatchAttempt(attempt=2, command="test", stderr="fail", passed=False),
            PatchAttempt(attempt=3, command="test", stderr="", passed=True),
        ]
        r.summary = "All tests passed after 3 attempt(s)"
        assert r.success is True
        assert len(r.attempts) == 3


class TestGeneratePatchPrompt:
    """Cover generate_patch_prompt method (lines 138-157)."""

    def test_generate_patch_prompt(self) -> None:
        """generate_patch_prompt returns a forcing prompt with stderr."""
        from half.forced_patch import ForcedPatchingLoop

        # We need a SandboxResult to pass in
        from half.sandbox_exec import SandboxResult

        result = SandboxResult(passed=False, stderr="AssertionError: test failed")
        result.stdout = "some output"
        result.commands_run = ["pytest"]
        result.exit_code = 1
        result.duration_seconds = 1.5

        loop = ForcedPatchingLoop(max_attempts=3)
        prompt = loop.generate_patch_prompt(result)
        assert "[FORCED PATCHING MODE]" in prompt
        assert "AssertionError: test failed" in prompt
        assert "You MUST fix ALL errors" in prompt

    def test_generate_patch_prompt_empty_stderr(self) -> None:
        """generate_patch_prompt handles empty stderr."""
        from half.forced_patch import ForcedPatchingLoop
        from half.sandbox_exec import SandboxResult

        result = SandboxResult(passed=True, stderr="")
        result.stdout = ""
        result.commands_run = []
        result.exit_code = 0
        result.duration_seconds = 0.0

        loop = ForcedPatchingLoop(max_attempts=3)
        prompt = loop.generate_patch_prompt(result)
        # Empty stderr will produce ` ``` ` with nothing between
        assert "```" in prompt
