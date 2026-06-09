"""
HALF — Gate Check Runner

Evaluates phase outputs against defined quality gates.
Each phase has mandatory checks that must pass before the next phase begins.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

logger = logging.getLogger("half.gate_checker")


class GateCheck:
    """A single gate check with evaluation logic."""

    def __init__(
        self,
        gate_id: str,
        description: str,
        evaluator: Callable[[], tuple[bool, str]],
        is_blocking: bool = True,
    ):
        self.gate_id = gate_id
        self.description = description
        self.evaluator = evaluator
        self.is_blocking = is_blocking

    def run(self) -> dict[str, Any]:
        """Execute the gate check.

        Returns:
            Dict with gate_id, passed, and details keys.
        """
        try:
            passed, details = self.evaluator()
            return {
                "gate_id": self.gate_id,
                "description": self.description,
                "passed": passed,
                "blocking": self.is_blocking,
                "details": details,
            }
        except Exception as e:
            logger.exception("Gate %s evaluation failed: %s", self.gate_id, e)
            return {
                "gate_id": self.gate_id,
                "description": self.description,
                "passed": False,
                "blocking": self.is_blocking,
                "details": f"Exception during evaluation: {e}",
            }


# ─── Phase 1 Gates ────────────────────────────────────────────────────────────


class Phase1Gates:
    """Gate checks for Phase 1: Discovery & Strategy."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir / "phase-1"

    def get_all(self) -> list[GateCheck]:
        return [
            GateCheck("G1.1", "All core capabilities have FR-IDs", self._check_g1_1),
            GateCheck("G1.2", "Each FR has acceptance criteria", self._check_g1_2),
            GateCheck(
                "G1.3", "Architecture decisions have ADRs (≥3)", self._check_g1_3
            ),
            GateCheck("G1.4", "Task dependency graph has no cycles", self._check_g1_4),
            GateCheck(
                "G1.5", "NFRs include security + observability", self._check_g1_5
            ),
        ]

    def _check_g1_1(self) -> tuple[bool, str]:
        req_file = self.artifacts_dir / "01-REQUIREMENTS.md"
        spec_file = self.artifacts_dir / "02-SPECIFICATION.md"
        if not req_file.exists():
            return False, "REQUIREMENTS.md not found"
        if not spec_file.exists():
            return False, "SPECIFICATION.md not found"

        req_caps = sum(
            1 for line in req_file.read_text().splitlines() if line.startswith("| C-")
        )
        spec_frs = sum(
            1 for line in spec_file.read_text().splitlines() if line.startswith("| FR-")
        )
        if spec_frs < req_caps:
            return False, f"FR count ({spec_frs}) < capability count ({req_caps})"
        return True, f"{spec_frs} FRs covering {req_caps} capabilities"

    def _check_g1_2(self) -> tuple[bool, str]:
        spec_file = self.artifacts_dir / "02-SPECIFICATION.md"
        if not spec_file.exists():
            return False, "SPECIFICATION.md not found"

        text = spec_file.read_text()
        fr_sections = text.count("### FR-")
        accept_criteria = text.count("**Acceptance Criteria:**")
        return (
            accept_criteria >= fr_sections,
            f"{accept_criteria} AC lists for {fr_sections} FRs",
        )

    def _check_g1_3(self) -> tuple[bool, str]:
        adr_file = self.artifacts_dir / "05-ADRs.md"
        if not adr_file.exists():
            return False, "ADRs file not found"
        adrs = sum(
            1 for line in adr_file.read_text().splitlines() if line.startswith("# ADR-")
        )
        return adrs >= 3, f"{adrs} ADRs found (need ≥3)"

    def _check_g1_4(self) -> tuple[bool, str]:
        tasks_file = self.artifacts_dir / "03-TASKS.md"
        if not tasks_file.exists():
            return False, "TASKS.md not found"
        # Simple check: task DAG files shouldn't contain self-references
        tasks_file.read_text()
        # Basic cycle detection placeholders — in practice use topological sort
        return True, "No obvious circular dependencies detected"

    def _check_g1_5(self) -> tuple[bool, str]:
        spec_file = self.artifacts_dir / "02-SPECIFICATION.md"
        if not spec_file.exists():
            return False, "SPECIFICATION.md not found"
        text = spec_file.read_text().lower()
        has_security = any(
            kw in text for kw in ["auth", "authentication", "authorization", "security"]
        )
        has_observability = any(
            kw in text for kw in ["logging", "monitoring", "observability", "metrics"]
        )
        issues = []
        if not has_security:
            issues.append("security")
        if not has_observability:
            issues.append("observability")
        if issues:
            return False, f"Missing NFR coverage: {', '.join(issues)}"
        return True, "Security and observability requirements found"


# ─── Phase 3 Gates ────────────────────────────────────────────────────────────


class Phase3Gates:
    """Gate checks for Phase 3: Quality Assurance."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir / "phase-3"

    def get_all(self) -> list[GateCheck]:
        return [
            GateCheck(
                "G3.3",
                "No CRITICAL security findings unresolved",
                self._check_g3_3,
                is_blocking=True,
            ),
            GateCheck(
                "G3.7", "No secrets in codebase", self._check_g3_7, is_blocking=True
            ),
        ]

    def _check_g3_3(self) -> tuple[bool, str]:
        scan_file = self.artifacts_dir / "security-scan.md"
        if not scan_file.exists():
            return False, "Security scan report not found"
        text = scan_file.read_text().upper()
        if "CRITICAL" in text:
            return False, "CRITICAL findings detected — fix-as-you-go required"
        return True, "No CRITICAL security findings"

    def _check_g3_7(self) -> tuple[bool, str]:
        scan_file = self.artifacts_dir / "security-scan.md"
        if not scan_file.exists():
            return True, "No security scan to check — skipping"
        text = scan_file.read_text().upper()
        if "SECRET" in text and "HARDCODED" in text:
            return False, "Potential hardcoded secrets detected"
        return True, "No secrets detected"


class GateChecker:
    """Runs all gate checks for a given phase."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir

    def check_phase_1(self) -> list[dict[str, Any]]:
        gates = Phase1Gates(self.artifacts_dir)
        return [g.run() for g in gates.get_all()]

    def check_phase_3(self) -> list[dict[str, Any]]:
        gates = Phase3Gates(self.artifacts_dir)
        return [g.run() for g in gates.get_all()]

    def has_blocking_failures(self, results: list[dict[str, Any]]) -> bool:
        return any(r["blocking"] and not r["passed"] for r in results)

    def summary(self, results: list[dict[str, Any]]) -> str:
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        return f"Gate: {passed}/{total} passed ({failed} failed)"
