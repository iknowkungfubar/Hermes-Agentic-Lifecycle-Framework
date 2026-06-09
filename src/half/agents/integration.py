"""
HALF-Integration Agent (Phase 3C)

Integration testing, contract verification, load testing, and failure mode testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContractCheck:
    """Verification of an API contract against the spec."""

    endpoint: str
    method: str
    status_code_match: bool = False
    response_schema_match: bool = False
    error_schema_match: bool = False


@dataclass
class IntegrationTestResult:
    """Result of an integration test suite run."""

    suite_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    contracts: list[ContractCheck] = field(default_factory=list)
    perf_p50_ms: float = 0.0
    perf_p95_ms: float = 0.0
    perf_p99_ms: float = 0.0


class IntegrationAgent:
    """Phase 3C: Integration and contract testing."""

    def __init__(self) -> None:
        self.results: list[IntegrationTestResult] = []

    def add_suite_result(
        self,
        suite_name: str,
        total: int,
        passed: int,
        failed: int = 0,
        skipped: int = 0,
    ) -> IntegrationTestResult:
        """Add an integration test suite result."""
        result = IntegrationTestResult(
            suite_name=suite_name,
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
        )
        self.results.append(result)
        return result

    def add_contract_check(
        self,
        suite_name: str,
        endpoint: str,
        method: str,
        status_ok: bool = False,
        schema_ok: bool = False,
        error_ok: bool = False,
    ) -> None:
        """Add a contract check to a suite result."""
        for result in self.results:
            if result.suite_name == suite_name:
                result.contracts.append(
                    ContractCheck(
                        endpoint=endpoint,
                        method=method,
                        status_code_match=status_ok,
                        response_schema_match=schema_ok,
                        error_schema_match=error_ok,
                    )
                )
                break

    def set_performance(
        self,
        suite_name: str,
        p50: float,
        p95: float,
        p99: float,
    ) -> None:
        """Set performance metrics for a suite."""
        for result in self.results:
            if result.suite_name == suite_name:
                result.perf_p50_ms = p50
                result.perf_p95_ms = p95
                result.perf_p99_ms = p99
                break

    def all_passed(self) -> bool:
        """Check if all suites passed."""
        return all(r.failed == 0 for r in self.results)

    def render_report_markdown(self) -> str:
        """Render the integration test report as markdown."""
        lines = [
            "# Integration Test Report",
            "",
            "**Test Run:** {timestamp}",
            "",
            "## Summary",
            "",
            "| Suite | Total | Passed | Failed | Skipped |",
            "|-------|-------|--------|--------|---------|",
        ]

        for r in self.results:
            lines.append(
                f"| {r.suite_name} | {r.total} | {r.passed} | "
                f"{r.failed} | {r.skipped} |"
            )

        # Contracts
        contracts = [c for r in self.results for c in r.contracts]
        if contracts:
            lines.extend(
                [
                    "",
                    "## Contract Verification",
                    "",
                    "| Endpoint | Status Code | Response Schema | Error Schema |",
                    "|----------|-------------|-----------------|--------------|",
                ]
            )
            for c in contracts:
                lines.append(
                    f"| {c.method} {c.endpoint} | "
                    f"{'✓' if c.status_code_match else '✗'} | "
                    f"{'✓' if c.response_schema_match else '✗'} | "
                    f"{'✓' if c.error_schema_match else '✗'} |"
                )

        # Performance
        perf_suites = [r for r in self.results if r.perf_p50_ms > 0]
        if perf_suites:
            lines.extend(
                [
                    "",
                    "## Performance",
                    "",
                    "| Suite | p50 | p95 | p99 |",
                    "|-------|-----|-----|-----|",
                ]
            )
            for r in perf_suites:
                lines.append(
                    f"| {r.suite_name} | {r.perf_p50_ms:.0f}ms | "
                    f"{r.perf_p95_ms:.0f}ms | {r.perf_p99_ms:.0f}ms |"
                )

        lines.extend(
            [
                "",
                "## Regression Check",
                f"- **{'PASS' if self.all_passed() else 'FAIL'}:** All suites passing",
            ]
        )

        return "\n".join(lines)
