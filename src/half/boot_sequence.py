"""HALF 1.5 — HALF 1.5 OS Boot Sequence.

Implements the 4-phase boot sequence for the HALF 1.5 Agentic OS:
Phase 1: Hardware Initialization & Identity Boot
Phase 2: Knowledge & Bus Initialization
Phase 3: Telemetry & GUI Scaffold
Phase 4: Master Genesis Prompt

Based on the HALF 1.5 doctrine's 'OS Boot Sequence' specification.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.boot")


@dataclass
class BootPhase:
    """Result of a boot phase."""

    phase: int
    name: str
    status: str  # pending, running, passed, failed, skipped
    checks: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    summary: str = ""


@dataclass
class BootReport:
    """Complete boot sequence report."""

    phases: list[BootPhase] = field(default_factory=list)
    overall_status: str = "pending"
    started_at: str = ""
    completed_at: str = ""


class BootSequence:
    """Executes the 4-phase HALF 1.5 OS boot sequence.

    Usage:
        boot = BootSequence()
        report = boot.run()
        if report.overall_status == "passed":
            print("HALF 1.5 Agentic OS is ready")
    """

    def __init__(self, config_dir: str | Path = ".hale"):
        self.config_dir = Path(config_dir)
        self.report = BootReport(started_at=datetime.now(tz=timezone.utc).isoformat())

    def run(self) -> BootReport:
        """Execute the complete boot sequence."""
        logger.info("Boot: Starting HALF 1.5 OS boot sequence")

        phases = [
            (1, "Hardware Initialization & Identity Boot", self._phase1_hardware),
            (2, "Knowledge & Bus Initialization", self._phase2_knowledge),
            (3, "Telemetry & GUI Scaffold", self._phase3_telemetry),
            (4, "Master Genesis Prompt", self._phase4_genesis),
        ]

        for phase_num, name, func in phases:
            now = datetime.now(tz=timezone.utc).isoformat()
            phase = BootPhase(phase=phase_num, name=name, status="running", started_at=now)
            try:
                func(phase)
                phase.status = "passed"
            except Exception as e:
                phase.status = "failed"
                phase.summary = str(e)
                logger.error("Boot: Phase %d failed: %s", phase_num, e)

            phase.completed_at = datetime.now(tz=timezone.utc).isoformat()
            self.report.phases.append(phase)

        all_passed = all(p.status == "passed" for p in self.report.phases)
        self.report.overall_status = "passed" if all_passed else "failed"
        self.report.completed_at = datetime.now(tz=timezone.utc).isoformat()

        logger.info("Boot: Sequence complete — %s", self.report.overall_status)
        return self.report

    def _phase1_hardware(self, phase: BootPhase) -> None:
        """Phase 1: Hardware Initialization & Identity Boot."""
        checks = []

        # 1.1: Check AMD ROCm driver
        try:
            result = subprocess.run(["rocminfo"], capture_output=True, text=True, timeout=15)
            rocm_ok = result.returncode == 0
            checks.append({
                "name": "rocm-driver",
                "status": "passed" if rocm_ok else "failed",
                "detail": "ROCm driver detected" if rocm_ok else "rocminfo not available",
            })
        except FileNotFoundError:
            checks.append({"name": "rocm-driver", "status": "skipped", "detail": "rocminfo not found"})

        # 1.2: Check disk space
        import shutil
        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            checks.append({
                "name": "disk-space",
                "status": "passed" if free_gb > 5 else "failed",
                "detail": f"{free_gb:.1f} GB free",
            })
        except Exception as e:
            checks.append({"name": "disk-space", "status": "failed", "detail": str(e)})

        # 1.3: Check Python version
        py = sys.version_info
        checks.append({
            "name": "python-version",
            "status": "passed" if py.major >= 3 and py.minor >= 13 else "failed",
            "detail": f"Python {py.major}.{py.minor}.{py.micro}",
        })

        # 1.4: Check git
        import shutil
        git = shutil.which("git")
        checks.append({
            "name": "git",
            "status": "passed" if git else "failed",
            "detail": f"git at {git}" if git else "git not found",
        })

        phase.checks = checks
        phase.summary = f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} checks passed"

    def _phase2_knowledge(self, phase: BootPhase) -> None:
        """Phase 2: Knowledge & Bus Initialization."""
        checks = []

        # 2.1: Initialize PGlite/KG context registry
        try:
            from half.pglite_registry import PGliteRegistry
            registry = PGliteRegistry(db_path=str(self.config_dir / "context-registry.db"))
            # Index the codebase
            total = registry.index_codebase("src")
            checks.append({
                "name": "context-registry",
                "status": "passed",
                "detail": f"Indexed {total} entities",
            })
        except Exception as e:
            checks.append({
                "name": "context-registry",
                "status": "warning",
                "detail": str(e)[:100],
            })

        # 2.2: Initialize Agent Mail
        try:
            from half.agent_mail.database import AgentMailDatabase
            db = AgentMailDatabase(db_path=str(self.config_dir / "agent-mail" / "mail.db"))
            checks.append({
                "name": "agent-mail",
                "status": "passed",
                "detail": "Agent Mail database initialized",
            })
        except Exception as e:
            checks.append({
                "name": "agent-mail",
                "status": "warning",
                "detail": str(e)[:100],
            })

        # 2.3: Check .harness/skills/
        skills_dir = self.config_dir.parent / ".harness" / "skills"
        if skills_dir.exists():
            skills = list(skills_dir.glob("*.md")) + list(skills_dir.glob("*.yaml"))
            checks.append({
                "name": "portable-skills",
                "status": "passed",
                "detail": f"{len(skills)} skill(s) found",
            })
        else:
            checks.append({
                "name": "portable-skills",
                "status": "info",
                "detail": "No skills dir — create .harness/skills/ for PSMs",
            })

        phase.checks = checks

    def _phase3_telemetry(self, phase: BootPhase) -> None:
        """Phase 3: Telemetry & GUI Scaffold."""
        checks = []

        # 3.1: Check if GUI binary exists
        gui_path = Path("src-tauri/target/release/half-command-center")
        checks.append({
            "name": "gui-binary",
            "status": "passed" if gui_path.exists() else "warning",
            "detail": f"GUI binary at {gui_path}" if gui_path.exists() else "Not built — run 'cd src-tauri && cargo build --release'",
        })

        # 3.2: Check Docker Compose
        foss_compose = Path("docker/docker-compose.foss.yml")
        checks.append({
            "name": "foss-stack-config",
            "status": "passed" if foss_compose.exists() else "warning",
            "detail": "docker-compose.foss.yml ready" if foss_compose.exists() else "Not found",
        })

        phase.checks = checks

    def _phase4_genesis(self, phase: BootPhase) -> None:
        """Phase 4: Master Genesis — print the startup prompt."""
        phase.checks = [{
            "name": "genesis-prompt",
            "status": "info",
            "detail": "System ready — input the Master Genesis Prompt to begin",
        }]
        phase.summary = "HALF 1.5 Agentic OS ready for input"

    def print_report(self) -> str:
        """Print the boot report.

        Returns:
            ASCII report string.
        """
        lines = [
            "╔═══════════════════════════════════════════════════╗",
            "║     HALF 1.5 Agentic OS — Boot Sequence          ║",
            "╚═══════════════════════════════════════════════════╝",
            f"  Overall: {self.report.overall_status.upper()}",
            "",
        ]
        for phase in self.report.phases:
            icon = {"passed": "✓", "failed": "✗", "running": "▶", "pending": "○", "skipped": "→", "warning": "!", "info": "i"}.get(phase.status, "?")
            lines.append(f"  [{icon}] Phase {phase.phase}: {phase.name}")
            for check in phase.checks:
                c_icon = {"passed": "✓", "failed": "✗", "warning": "!", "info": "i", "skipped": "-"}.get(check["status"], "?")
                lines.append(f"       [{c_icon}] {check['name']:30} {check.get('detail', '')[:60]}")
        lines.append("")
        return "\n".join(lines)
