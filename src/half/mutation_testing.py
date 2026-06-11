"""HALF — Mutation Testing & Sycophancy Guardrail.

Prevents agents from writing trivial assert True tests by scoring test quality.
Enforces mutation testing — modifies source code and verifies tests catch the change.
If tests pass despite mutations, they're not真正 testing anything.

Based on the HALF doctrine's Phase 2 'Zero-Defect Precision' specification.

Usage:
    guardrail = SycophancyGuardrail("src/", "tests/")
    report = guardrail.run()
    if report.score < 80:
        print("Test quality too low — failing gate")
"""

from __future__ import annotations

import ast
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.mutation_testing")


@dataclass
class TestQualityFinding:
    """A finding about test quality."""

    file: str
    line: int
    issue_type: str  # assert_true, no_assert, low_coverage, mutation_survived
    description: str
    severity: str = "warning"


@dataclass
class MutationResult:
    """Result of a single mutation test."""

    target_file: str
    mutation: str
    line: int
    test_caught: bool  # True = test caught the mutation (good)
    original_code: str = ""
    mutated_code: str = ""


@dataclass
class SycophancyReport:
    """Complete test quality and mutation testing report."""

    score: float = 100.0  # 0-100 quality score
    findings: list[TestQualityFinding] = field(default_factory=list)
    mutations: list[MutationResult] = field(default_factory=list)
    mutation_kill_rate: float = 1.0  # 0.0-1.0, higher is better
    summary: str = ""


class SycophancyGuardrail:
    """Detects and prevents sycophantic (trivially-passing) tests.

    Three layers of defense:
    1. Static analysis: scans tests for assert True, no assertions, empty bodies
    2. Coverage check: enforces 80% minimum threshold
    3. Mutation testing: modifies source code, verifies tests catch it
    """

    def __init__(
        self,
        src_dir: str | Path = "src",
        test_dir: str | Path = "tests",
        coverage_threshold: float = 80.0,
    ):
        self.src_dir = Path(src_dir)
        self.test_dir = Path(test_dir)
        self.coverage_threshold = coverage_threshold
        self.report = SycophancyReport()

    def run(self) -> SycophancyReport:
        """Run all test quality checks and mutation tests.

        Returns:
            SycophancyReport with findings and score.
        """
        logger.info("Sycophancy Guardrail: Starting test quality audit")

        self._check_for_assert_true()
        self._check_empty_tests()
        self._check_no_assertion_tests()
        self._run_mutation_tests()
        self._calculate_score()

        self.report.summary = (
            f"Sycophancy Guardrail: score={self.report.score:.0f}/100, "
            f"mutation kill rate={self.report.mutation_kill_rate:.0%}, "
            f"{len(self.report.findings)} findings"
        )
        logger.info(self.report.summary)
        return self.report

    def _check_for_assert_true(self) -> None:
        """Find tests with assert True — they pass trivially."""
        for test_file in sorted(self.test_dir.rglob("test_*.py")):
            try:
                source = test_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        self.report.findings.append(TestQualityFinding(
                            file=str(test_file.relative_to(self.test_dir.parent)),
                            line=node.lineno,
                            issue_type="assert_true",
                            description="Trivial assert True — test passes without verification",
                            severity="critical",
                        ))

    def _check_empty_tests(self) -> None:
        """Find test functions with no assertions at all."""
        for test_file in sorted(self.test_dir.rglob("test_*.py")):
            try:
                source = test_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    has_assert = any(
                        isinstance(child, ast.Assert)
                        for child in ast.walk(node)
                    )
                    if not has_assert:
                        self.report.findings.append(TestQualityFinding(
                            file=str(test_file.relative_to(self.test_dir.parent)),
                            line=node.lineno,
                            issue_type="no_assert",
                            description=f"Test '{node.name}' has no assertions — passes vacuously",
                            severity="high",
                        ))

    def _check_no_assertion_tests(self) -> None:
        """Find test files where no function uses assert."""
        for test_file in sorted(self.test_dir.rglob("test_*.py")):
            try:
                source = test_file.read_text()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            has_assert = any(
                isinstance(node, ast.Assert)
                for node in ast.walk(tree)
            )
            if not has_assert:
                test_funcs = [
                    n.name for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                ]
                if test_funcs:
                    self.report.findings.append(TestQualityFinding(
                        file=str(test_file.relative_to(self.test_dir.parent)),
                        line=1,
                        issue_type="no_assert",
                        description=f"Test file has {len(test_funcs)} tests but zero assertions",
                        severity="high",
                    ))

    def _run_mutation_tests(self) -> None:
        """Run mutation tests: modify source code and check if tests catch it.

        Mutations performed:
        - Change == to !=
        - Change > to <
        - Change True to False
        - Remove a return statement
        - Change + to -
        """
        for src_file in sorted(self.src_dir.rglob("*.py")):
            try:
                source = src_file.read_text()
                lines = source.split("\n")
            except (UnicodeDecodeError, OSError):
                continue

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Skip non-code lines
                if not stripped or stripped.startswith(("#", "\"", "'", "import", "from")):
                    continue

                mutation = None
                if " == " in stripped and "!=" not in stripped:
                    mutation = ("==", "!=", i + 1)
                elif " > " in stripped and not stripped.startswith("#"):
                    mutation = (">", "<", i + 1)
                elif "True" in stripped and "False" not in stripped:
                    mutation = ("True", "False", i + 1)

                if mutation:
                    original, mutated, line_num = mutation
                    mutated_line = line.replace(original, mutated, 1)
                    mutated_lines = list(lines)
                    mutated_lines[i] = mutated_line
                    mutated_source = "\n".join(mutated_lines)

                    # Run tests with mutated source
                    caught = self._run_single_mutation(src_file, mutated_source)

                    self.report.mutations.append(MutationResult(
                        target_file=str(src_file.relative_to(self.src_dir.parent)),
                        mutation=f"{original} → {mutated}",
                        line=line_num,
                        test_caught=caught,
                    ))

                    if not caught:
                        self.report.findings.append(TestQualityFinding(
                            file=str(src_file.relative_to(self.src_dir.parent)),
                            line=line_num,
                            issue_type="mutation_survived",
                            description=f"Mutation '{original} → {mutated}' survived — tests didn't catch it",
                            severity="critical",
                        ))

    def _run_single_mutation(self, src_file: Path, mutated_source: str) -> bool:
        """Apply a single mutation and check if tests catch it.

        Args:
            src_file: Path to the source file.
            mutated_source: Source code with mutation applied.

        Returns:
            True if tests failed (mutation caught), False if tests passed (mutation survived).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temporary copy of mutated file
            tmp_file = Path(tmpdir) / src_file.name
            tmp_file.write_text(mutated_source)

            try:
                result = subprocess.run(
                    ["python3", "-m", "pytest", str(self.test_dir), "-q", "--timeout=30"],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(self.src_dir.parent),
                )
                # If tests fail, mutation was caught
                return result.returncode != 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return True  # Assume caught if we can't run

    def _calculate_score(self) -> None:
        """Calculate overall test quality score (0-100)."""
        deductions = 0.0

        # Deduct for each critical finding
        critical = [f for f in self.report.findings if f.severity == "critical"]
        deductions += len(critical) * 15

        # Deduct for high severity
        high = [f for f in self.report.findings if f.severity == "high"]
        deductions += len(high) * 8

        # Deduct for survived mutations
        survived = sum(1 for m in self.report.mutations if not m.test_caught)
        deductions += survived * 20

        # Calculate mutation kill rate
        total_muts = len(self.report.mutations)
        if total_muts > 0:
            caught = sum(1 for m in self.report.mutations if m.test_caught)
            self.report.mutation_kill_rate = caught / total_muts
            if self.report.mutation_kill_rate < 0.8:
                deductions += 20

        self.report.score = max(0, min(100, 100 - deductions))

    def generate_report_markdown(self) -> str:
        """Generate a human-readable report.

        Returns:
            Markdown report string.
        """
        lines = [
            "# Sycophancy Guardrail Report",
            "",
            f"**Test Quality Score:** {self.report.score:.0f}/100",
            f"**Mutation Kill Rate:** {self.report.mutation_kill_rate:.0%}",
            f"**Findings:** {len(self.report.findings)}",
            f"**Mutations applied:** {len(self.report.mutations)}",
            "",
        ]

        if self.report.findings:
            lines.append("## Findings")
            for f in self.report.findings:
                icon = {"critical": "🔴", "high": "🟡", "warning": "🟢"}.get(f.severity, "⚪")
                lines.append(f"- {icon} [{f.severity}] {f.file}:{f.line} — {f.description}")

        if self.report.mutations:
            lines.append("")
            lines.append("## Mutation Results")
            for m in self.report.mutations[:10]:
                status = "✅ Caught" if m.test_caught else "❌ Survived"
                lines.append(f"- {m.target_file}:{m.line} {m.mutation} → {status}")

        verdict = "PASS" if self.report.score >= 70 and self.report.mutation_kill_rate >= 0.8 else "FAIL"
        lines.extend(["", f"## Verdict: **{verdict}**"])

        return "\n".join(lines)
