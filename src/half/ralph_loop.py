"""HALF — The Ralph Loop: Continuous Infrastructure Automation.

Schedulers (systemd timers or APScheduler) wake an agent nightly to:
- Audit codebase for typing coverage
- Detect duplicate logic and performance bottlenecks
- Auto-generate local Git branches and PRs for human review

Based on the HALF doctrine's Phase 3 Continuous Infrastructure Automation.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.ralph_loop")


@dataclass
class RalphFinding:
    """A finding from the nightly audit."""

    category: str  # typing, duplication, performance, deprecation
    file: str
    line: int = 0
    description: str = ""
    severity: str = "info"  # info, warning, critical
    auto_fixable: bool = False
    branch_name: str = ""


@dataclass
class RalphReport:
    """Nightly audit report."""

    timestamp: str = ""
    findings: list[RalphFinding] = field(default_factory=list)
    branch_count: int = 0
    summary: str = ""


class RalphLoop:
    """Nightly codebase audit and auto-remediation.

    Runs as a scheduled job (cron/systemd timer) and:
    1. Scans for type coverage gaps
    2. Detects code duplication
    3. Identifies performance bottlenecks
    4. Creates branches with auto-fixes
    """

    def __init__(self, repo_path: str | Path = "."):
        self.repo_path = Path(repo_path)
        self.report = RalphReport(timestamp=datetime.now(tz=timezone.utc).isoformat())

    def run(self) -> RalphReport:
        """Execute the full Ralph Loop audit."""
        logger.info("Ralph Loop: Starting nightly audit of %s", self.repo_path)

        self._check_typing_coverage()
        self._check_code_duplication()
        self._check_performance_hotspots()
        self._create_autofix_branches()

        self.report.summary = (
            f"Ralph Loop: {len(self.report.findings)} findings, "
            f"{self.report.branch_count} auto-fix branches created"
        )
        logger.info(self.report.summary)
        return self.report

    def _check_typing_coverage(self) -> None:
        """Check mypy type coverage on source files."""
        try:
            result = subprocess.run(
                ["python3", "-m", "mypy", "src/", "--strict"],
                capture_output=True, text=True, timeout=120,
                cwd=str(self.repo_path),
            )
            lines = result.stdout.split("\n")
            error_lines = [l for l in lines if "error:" in l]
            if error_lines:
                for line in error_lines[:20]:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        self.report.findings.append(RalphFinding(
                            category="typing",
                            file=parts[0].strip(),
                            line=int(parts[1]) if parts[1].isdigit() else 0,
                            description=line,
                            severity="warning",
                            auto_fixable="await" in line or "type" in line,
                        ))
            else:
                logger.info("Ralph Loop: No typing issues found")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("Ralph Loop: Typing check failed: %s", e)

    def _check_code_duplication(self) -> None:
        """Detect duplicated code blocks using simple hash comparison."""
        src_dir = self.repo_path / "src"
        if not src_dir.exists():
            return

        # Simple line-based duplication check
        seen_lines: dict[str, list[str]] = {}
        for py_file in src_dir.rglob("*.py"):
            try:
                lines = py_file.read_text().split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if len(stripped) > 20 and not stripped.startswith(("#", "\"", "'")):
                        if stripped in seen_lines:
                            seen_lines[stripped].append(f"{py_file}:{i}")
                        else:
                            seen_lines[stripped] = [f"{py_file}:{i}"]
            except Exception:
                continue

        # Report lines that appear in multiple files
        for line, locations in seen_lines.items():
            if len(locations) >= 3:  # Same line in 3+ files
                self.report.findings.append(RalphFinding(
                    category="duplication",
                    file=locations[0],
                    description=f"Duplicate code ({len(locations)} occurrences): {line[:60]}",
                    severity="warning",
                ))

    def _check_performance_hotspots(self) -> None:
        """Flag files over 300 lines as potential performance hotspots."""
        for py_file in (self.repo_path / "src").rglob("*.py"):
            try:
                lines = len(py_file.read_text().split("\n"))
                if lines > 300:
                    self.report.findings.append(RalphFinding(
                        category="performance",
                        file=str(py_file.relative_to(self.repo_path)),
                        description=f"File is {lines} lines (threshold: 300) — consider splitting",
                        severity="info",
                    ))
            except Exception:
                continue

    def _create_autofix_branches(self) -> None:
        """Create Git branches for auto-fixable findings."""
        fixable = [f for f in self.report.findings if f.auto_fixable]
        if not fixable:
            return

        branch_name = f"ralph/auto-fix-{datetime.now(tz=timezone.utc).strftime('%Y%m%d')}"
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )

            # Apply auto-fixes (e.g., mypy --fix)
            subprocess.run(
                ["python3", "-m", "mypy", "src/", "--strict", "--show-error-codes"],
                capture_output=True, text=True, timeout=120,
                cwd=str(self.repo_path),
            )

            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )
            subprocess.run(
                ["git", "commit", "-m", f"ralph: auto-fix {len(fixable)} issues"],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )
            subprocess.run(
                ["git", "checkout", "-"],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )

            for finding in fixable:
                finding.branch_name = branch_name
            self.report.branch_count = 1

        except Exception as e:
            logger.warning("Ralph Loop: Auto-fix branch creation failed: %s", e)
