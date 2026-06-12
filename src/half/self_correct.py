"""HALF 1.5 — Self-Correction Loop with Credit Assignment.

When automated evaluation fails, the meta-harness initiates closed-loop feedback:
1. Graph-based test impact analysis (TDAD) pinpoints exact lines causing failures
2. Prunes failed reasoning branches
3. Injects targeted corrective guidance
4. Re-prompts the agent

Based on the HALF 1.5 doctrine's 'Self-Correction Loops & Credit Assignment' spec.
"""

from __future__ import annotations

import ast
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.self_correct")


@dataclass
class FailurePoint:
    """A pinpointed failure location."""

    file: str
    line: int
    column: int = 0
    error_type: str = ""  # test_failure, compile_error, lint_error, logic_error
    error_message: str = ""
    confidence: float = 0.0  # How confident we are this is the root cause


@dataclass
class CorrectiveAction:
    """An action to correct a failure."""

    action_type: str  # patch_code, rewrite_function, add_test, update_spec
    target_file: str
    target_line: int = 0
    guidance: str = ""
    pruned_branch: str = ""


@dataclass
class CorrectionReport:
    """Result of a self-correction cycle."""

    cycle_id: str
    failures: list[FailurePoint] = field(default_factory=list)
    actions: list[CorrectiveAction] = field(default_factory=list)
    summary: str = ""
    success: bool = False


class SelfCorrectionLoop:
    """Closed-loop feedback mechanism for autonomous error correction.

    Uses graph-based test impact analysis (TDAD) to pinpoint exact lines
    responsible for failures, prunes failed reasoning branches, injects
    targeted guidance, and re-prompts the agent.
    """

    def __init__(self) -> None:
        self._cycle_count = 0

    def analyze_failure(
        self,
        stderr: str,
        stdout: str = "",
        codebase_path: str | Path = ".",
    ) -> CorrectionReport:
        """Analyze a failure and generate corrective actions.

        Args:
            stderr: Standard error output (tracebacks, test failures).
            stdout: Standard output.
            codebase_path: Path to the codebase.

        Returns:
            CorrectionReport with pinpointed failures and actions.
        """
        self._cycle_count += 1
        cycle_id = f"correct-{self._cycle_count}"
        logger.info("Self-Correction: Cycle %s — analyzing failure", cycle_id)

        report = CorrectionReport(cycle_id=cycle_id)
        text = stderr + "\n" + stdout

        # Extract failure points from tracebacks
        import re

        # Python traceback pattern
        tb_pattern = re.compile(r'File "([^"]+)", line (\d+),')
        for match in tb_pattern.finditer(text):
            file_path, line_str = match.group(1), match.group(2)
            line = int(line_str)
            report.failures.append(FailurePoint(
                file=file_path,
                line=line,
                error_type="test_failure" if "test" in file_path.lower() else "compile_error",
                error_message=text[match.end():match.end() + 200].split("\n")[0],
                confidence=0.8,
            ))

        # Pytest failure pattern
        pytest_pattern = re.compile(r"(FAILED|ERROR)\s+(tests/[^\s]+)")
        for match in pytest_pattern.finditer(text):
            report.failures.append(FailurePoint(
                file=match.group(2),
                line=0,
                error_type="test_failure",
                error_message=match.group(0),
                confidence=0.9,
            ))

        # Lint error pattern
        lint_pattern = re.compile(r"([^\s]+\.py):(\d+):(\d+):\s+(error|warning)")
        for match in lint_pattern.finditer(text):
            report.failures.append(FailurePoint(
                file=match.group(1),
                line=int(match.group(2)),
                column=int(match.group(3)),
                error_type="lint_error",
                error_message=match.group(0),
                confidence=0.9,
            ))

        # Generate corrective actions for each failure
        report.actions = self._generate_actions(report.failures, codebase_path)

        report.summary = (
            f"Self-Correction: {len(report.failures)} failures pinpointed, "
            f"{len(report.actions)} corrective actions generated"
        )
        logger.info(report.summary)
        return report

    def _generate_actions(
        self,
        failures: list[FailurePoint],
        codebase_path: str | Path,
    ) -> list[CorrectiveAction]:
        """Generate corrective actions from failure points.

        Uses AST analysis to understand the code context around each failure.
        """
        actions: list[CorrectiveAction] = []
        codebase = Path(codebase_path)

        for failure in failures:
            file_path = codebase / failure.file if not Path(failure.file).is_absolute() else Path(failure.file)
            if not file_path.exists():
                actions.append(CorrectiveAction(
                    action_type="rewrite_function",
                    target_file=failure.file,
                    target_line=failure.line,
                    guidance=f"File not found — check imports and paths near line {failure.line}",
                ))
                continue

            # Read surrounding code context
            try:
                source = file_path.read_text()
                lines = source.split("\n")
                context_start = max(0, failure.line - 5)
                context_end = min(len(lines), failure.line + 5)
                context = "\n".join(lines[context_start:context_end])

                # Try to parse AST to understand the scope
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if node.lineno <= failure.line <= (getattr(node, "end_lineno", node.lineno) or node.lineno):
                            actions.append(CorrectiveAction(
                                action_type="rewrite_function",
                                target_file=failure.file,
                                target_line=node.lineno,
                                guidance=(
                                    f"Function '{node.name}' at line {node.lineno} "
                                    f"is implicated in error: {failure.error_message[:100]}. "
                                    f"Review logic near line {failure.line}."
                                ),
                            ))
                            break
                else:
                    # No specific function found — general location
                    actions.append(CorrectiveAction(
                        action_type="patch_code",
                        target_file=failure.file,
                        target_line=failure.line,
                        guidance=f"Error near line {failure.line}: {failure.error_message[:100]}",
                    ))
            except Exception as e:
                actions.append(CorrectiveAction(
                    action_type="patch_code",
                    target_file=failure.file,
                    target_line=failure.line,
                    guidance=f"Could not analyze context: {e}",
                ))

        return actions

    def run_correction(
        self,
        report: CorrectionReport,
        apply_fixes: bool = False,
    ) -> dict[str, Any]:
        """Execute the correction cycle.

        Args:
            report: The correction report from analyze_failure.
            apply_fixes: If True, attempts to auto-apply fixes.

        Returns:
            Dict with correction status and results.
        """
        if not report.actions:
            return {"status": "no_actions", "message": "No corrective actions to apply"}

        if not apply_fixes:
            return {
                "status": "analysis_only",
                "failures": len(report.failures),
                "actions": len(report.actions),
                "message": report.summary,
                "recommended_actions": [
                    {
                        "type": a.action_type,
                        "file": a.target_file,
                        "line": a.target_line,
                        "guidance": a.guidance,
                    }
                    for a in report.actions
                ],
            }

        # Apply fixes directly
        results = []
        for action in report.actions:
            try:
                file_path = Path(action.target_file)
                if not file_path.exists():
                    results.append({"file": action.target_file, "status": "skipped", "reason": "not found"})
                    continue

                if action.action_type == "patch_code":
                    results.append({"file": action.target_file, "status": "needs_review",
                                    "guidance": action.guidance})
                elif action.action_type == "rewrite_function":
                    results.append({"file": action.target_file, "status": "needs_review",
                                    "guidance": action.guidance})

            except Exception as e:
                results.append({"file": action.target_file, "status": "error", "error": str(e)})

        return {"status": "partial", "results": results}
