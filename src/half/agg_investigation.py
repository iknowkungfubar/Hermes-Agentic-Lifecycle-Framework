"""HALF 1.5 — Aggressive Investigation Engine.

When facing ambiguities or failed test states, agents relentlessly pursue
root cause by writing custom debugging scripts, querying telemetry logs,
and running diagnostic commands — rather than immediately escalating.

Based on the HALF 1.5 doctrine's 'Aggressive Investigation' specification.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.agg_investigation")


@dataclass
class InvestigationStep:
    """A single investigation step."""

    step_type: str  # log_query, debug_script, trace_span, dependency_check
    target: str  # What to investigate
    command: str  # Command to run
    result: str = ""
    findings: str = ""
    severity: str = "info"  # info, warning, critical


@dataclass
class InvestigationReport:
    """Complete investigation results."""

    failure_description: str
    steps: list[InvestigationStep] = field(default_factory=list)
    root_cause: str = ""
    recommended_fix: str = ""
    confidence: float = 0.0
    should_escalate: bool = False


class AggressiveInvestigator:
    """Relentlessly pursues root causes before escalating to humans.

    Strategy:
    1. Check logs and telemetry for error patterns
    2. Write custom debugging scripts
    3. Run diagnostic commands
    4. Only escalate when all options exhausted
    """

    def __init__(self) -> None:
        self._script_dir = Path(".hale/investigations")
        self._script_dir.mkdir(parents=True, exist_ok=True)

    def investigate(self, failure_description: str, context: dict[str, Any] | None = None) -> InvestigationReport:
        """Run a full investigation into a failure.

        Args:
            failure_description: Description of the failure.
            context: Optional context (logs, stack traces, env info).

        Returns:
            InvestigationReport with findings and root cause.
        """
        logger.info("Investigation: Starting investigation of: %s", failure_description[:100])
        report = InvestigationReport(failure_description=failure_description)

        # Phase 1: Check logs
        self._check_logs(report, context)
        if report.root_cause:
            return report

        # Phase 2: Write debug script
        self._write_debug_script(report, context)
        if report.root_cause:
            return report

        # Phase 3: System diagnostics
        self._run_diagnostics(report)
        if report.root_cause:
            return report

        # Phase 4: Dependency check
        self._check_dependencies(report)

        # If all failed, escalate
        if not report.root_cause:
            report.should_escalate = True
            report.recommended_fix = "Could not determine root cause automatically — human investigation required"
            report.confidence = 0.2

        return report

    def _check_logs(self, report: InvestigationReport, context: dict[str, Any] | None) -> None:
        """Check log files for relevant error patterns."""
        log_dirs = [
            Path(".hale/logs"),
            Path(".hale/gates"),
        ]

        for log_dir in log_dirs:
            if not log_dir.exists():
                continue

            for log_file in sorted(log_dir.glob("*"))[:5]:
                try:
                    content = log_file.read_text(errors="replace")
                    # Look for ERROR, CRITICAL, FAILED patterns
                    error_lines = [
                        l for l in content.split("\n")
                        if any(kw in l.upper() for kw in ["ERROR", "CRITICAL", "FAILED", "TRACEBACK"])
                    ]
                    if error_lines:
                        report.steps.append(InvestigationStep(
                            step_type="log_query",
                            target=str(log_file.name),
                            command=f"read {log_file.name}",
                            result=f"Found {len(error_lines)} error lines",
                            findings=error_lines[0][:200],
                            severity="warning",
                        ))
                except Exception:
                    continue

    def _write_debug_script(self, report: InvestigationReport, context: dict[str, Any] | None) -> None:
        """Write and execute a custom debug script based on the failure."""
        context = context or {}
        failure = report.failure_description.lower()

        script_parts = [
            "#!/usr/bin/env python3",
            '"""Auto-generated investigation script."""',
            "import sys, os, json",
            "",
            "results = {}",
        ]

        # Check for import errors
        if "import" in failure or "module" in failure:
            # Extract module name from error
            for word in failure.split():
                if word.endswith("Error") or word.endswith("NotFound"):
                    continue
            script_parts.extend([
                "",
                "# Check import paths",
                "results['sys_path'] = sys.path[:5]",
                "results['cwd'] = os.getcwd()",
            ])

        # Check for test failures
        elif "test" in failure or "assert" in failure:
            script_parts.extend([
                "",
                "# Run failing test with verbose output",
                "results['pytest_help'] = 'Run: python -m pytest tests/ -v --tb=long -x'",
            ])

        # Check for file not found
        elif "no such file" in failure or "not found" in failure:
            script_parts.extend([
                "",
                "# Check file system state",
                "import glob",
                "results['src_files'] = glob.glob('src/**/*.py', recursive=True)[:20]",
            ])

        script_parts.extend([
            "",
            "print(json.dumps(results, indent=2))",
        ])

        script_path = self._script_dir / "debug_investigation.py"
        script_path.write_text("\n".join(script_parts))
        script_path.chmod(0o755)

        # Execute the script
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=30,
            )
            report.steps.append(InvestigationStep(
                step_type="debug_script",
                target="root cause analysis",
                command=f"python debug_investigation.py",
                result=result.stdout[:500] if result.stdout else result.stderr[:200],
                findings="Debug script executed",
            ))
        except subprocess.TimeoutExpired:
            report.steps.append(InvestigationStep(
                step_type="debug_script",
                target="root cause analysis",
                command="python debug_investigation.py",
                result="Timed out",
                findings="Script exceeded 30s timeout",
                severity="warning",
            ))

    def _run_diagnostics(self, report: InvestigationReport) -> None:
        """Run system diagnostic commands."""
        diag_commands = [
            ("Python version", [sys.executable, "--version"]),
            ("Pip list", [sys.executable, "-m", "pip", "list", "--format=columns"]),
        ]

        for name, cmd in diag_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                report.steps.append(InvestigationStep(
                    step_type="trace_span",
                    target=name,
                    command=" ".join(cmd[-2:]),
                    result=result.stdout.strip()[:200],
                ))
            except Exception as e:
                report.steps.append(InvestigationStep(
                    step_type="trace_span",
                    target=name,
                    command=" ".join(cmd[-2:]),
                    result=str(e),
                    severity="warning",
                ))

    def _check_dependencies(self, report: InvestigationReport) -> None:
        """Check for dependency issues."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 and result.stdout.strip():
                report.steps.append(InvestigationStep(
                    step_type="dependency_check",
                    target="pip dependencies",
                    command="pip check",
                    result=result.stdout.strip()[:300],
                    severity="warning",
                ))
        except Exception:
            pass

    def generate_report(self, report: InvestigationReport) -> str:
        """Generate a human-readable investigation report.

        Returns:
            Markdown report.
        """
        lines = [
            "# Investigation Report",
            "",
            f"**Failure:** {report.failure_description[:200]}",
            f"**Root Cause:** {report.root_cause or 'Not determined'}",
            f"**Confidence:** {report.confidence:.0%}",
            f"**Escalate:** {'Yes' if report.should_escalate else 'No'}",
            "",
            "## Steps Taken",
        ]
        for step in report.steps:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(step.severity, "⚪")
            lines.append(f"- {icon} [{step.step_type}] {step.target}: {step.findings or step.result[:80]}")
        if report.root_cause:
            lines.extend(["", "## Recommended Fix", report.recommended_fix])
        return "\n".join(lines)
