"""
HALF-Testing Agent (Phase 3A)

Ensures test suite completeness by mapping FRs to test coverage,
generating gap tests, and producing a quality report.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FRTestCoverage:
    """Coverage of a functional requirement by tests."""

    fr_id: str
    happy_path_test: bool = False
    error_condition_tests: list[str] = field(default_factory=list)
    edge_case_tests: list[str] = field(default_factory=list)
    property_based_test: bool = False


@dataclass
class TestQualityReport:
    """Report on test suite quality."""

    total_tests: int = 0
    fr_coverage: int = 0
    total_frs: int = 0
    line_coverage_pct: float = 0.0
    branch_coverage_pct: float = 0.0
    gap_frs: list[str] = field(default_factory=list)


class TestingAgent:
    """Phase 3A: Test suite completeness verification and gap filling."""

    def __init__(self) -> None:
        self.coverage: dict[str, FRTestCoverage] = {}

    def add_fr(self, fr_id: str) -> None:
        """Register an FR for coverage tracking."""
        if fr_id not in self.coverage:
            self.coverage[fr_id] = FRTestCoverage(fr_id=fr_id)

    def record_happy_path(self, fr_id: str, test_name: str) -> None:
        """Record that an FR has a happy path test."""
        if fr_id in self.coverage:
            self.coverage[fr_id].happy_path_test = True

    def record_error_test(self, fr_id: str, test_name: str) -> None:
        """Record an error condition test for an FR."""
        if fr_id in self.coverage:
            self.coverage[fr_id].error_condition_tests.append(test_name)

    def record_edge_case(self, fr_id: str, test_name: str) -> None:
        """Record an edge case test for an FR."""
        if fr_id in self.coverage:
            self.coverage[fr_id].edge_case_tests.append(test_name)

    def generate_quality_report(self) -> TestQualityReport:
        """Generate a test quality report from coverage data."""
        total_frs = len(self.coverage)
        covered_frs = sum(
            1
            for c in self.coverage.values()
            if c.happy_path_test and len(c.error_condition_tests) > 0
        )
        gap_frs = [c.fr_id for c in self.coverage.values() if not c.happy_path_test]

        return TestQualityReport(
            total_tests=sum(
                1 + len(c.error_condition_tests) + len(c.edge_case_tests)
                for c in self.coverage.values()
            ),
            fr_coverage=covered_frs,
            total_frs=total_frs,
            gap_frs=gap_frs,
        )

    @staticmethod
    def derive_tests_from_fr(fr_id: str, description: str) -> list[str]:
        """Derive test cases from an FR description.

        Uses rules:
        - Happy path: test_<name>_success
        - Each error condition: test_<name>_<error>
        - Each edge case: test_<name>_<edge>
        - Property-based: test_<name>_property

        Args:
            fr_id: FR identifier.
            description: FR description text.

        Returns:
            List of test function names.
        """
        name = fr_id.lower().replace("-", "_")
        tests = [
            f"test_{name}_success",
            f"test_{name}_invalid_input",
            f"test_{name}_unauthorized",
        ]

        if "register" in description.lower() or "create" in description.lower():
            tests.extend(
                [
                    f"test_{name}_duplicate",
                    f"test_{name}_validation_error",
                ]
            )

        if "login" in description.lower() or "auth" in description.lower():
            tests.extend(
                [
                    f"test_{name}_wrong_password",
                    f"test_{name}_rate_limit",
                    f"test_{name}_token_expiry",
                ]
            )

        tests.append(f"test_{name}_property")
        return tests

    def render_report_markdown(self, report: TestQualityReport) -> str:
        """Render a test quality report as markdown."""
        lines = [
            "# Test Quality Report",
            "",
            "## Summary",
            f"- **Total Tests:** {report.total_tests}",
            f"- **FR Coverage:** {report.fr_coverage}/{report.total_frs}",
            f"- **Line Coverage:** {report.line_coverage_pct:.1f}%",
            f"- **Branch Coverage:** {report.branch_coverage_pct:.1f}%",
            "",
            "## FR Coverage Matrix",
            "",
            "| FR ID | Happy Path | Error Tests | Edge Cases | Property Test | Status |",
            "|-------|-----------|-------------|------------|---------------|--------|",
        ]
        for c in self.coverage.values():
            happy = "X" if c.happy_path_test else "-"
            prop = "X" if c.property_based_test else "-"
            status = "COVERED" if c.happy_path_test else "GAP"
            lines.append(
                f"| {c.fr_id} | {happy} | {len(c.error_condition_tests)} | "
                f"{len(c.edge_case_tests)} | {prop} | {status} |"
            )
        lines.extend(
            [
                "",
                "## Gaps",
                "",
            ]
        )
        if not report.gap_frs:
            lines.append("No gaps found.")
        else:
            lines.append("Uncovered FRs:")
            for fr in report.gap_frs:
                lines.append(f"- {fr}")
        return "\n".join(lines)
