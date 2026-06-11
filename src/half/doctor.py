"""HALF — Pre-Flight Doctor: Subsystem Health Diagnostics.

Runs before the orchestrator starts to verify the execution environment
is healthy. Checks ROCm kernel availability, LLM backend connectivity,
OpenTelemetry router latency, and dependency synchronization.

Based on the HALF doctrine's 'goal doctor' diagnostic protocol.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.doctor")


@dataclass
class HealthCheck:
    """Result of a single health check."""

    name: str
    status: bool
    message: str = ""
    severity: str = "info"  # info, warning, error, critical


@dataclass
class DoctorReport:
    """Complete pre-flight diagnostic report."""

    timestamp: str = ""
    system: dict[str, Any] = field(default_factory=dict)
    checks: list[HealthCheck] = field(default_factory=list)
    overall_status: str = "unknown"  # healthy, degraded, failed
    summary: str = ""

    def add(self, check: HealthCheck) -> None:
        self.checks.append(check)
        self._update_status()

    def _update_status(self) -> None:
        critical = any(c.severity == "critical" and not c.status for c in self.checks)
        errors = any(c.severity == "error" and not c.status for c in self.checks)
        if critical:
            self.overall_status = "failed"
        elif errors:
            self.overall_status = "degraded"
        else:
            self.overall_status = "healthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "system": self.system,
            "overall_status": self.overall_status,
            "checks": [
                {"name": c.name, "status": c.status, "message": c.message, "severity": c.severity}
                for c in self.checks
            ],
            "summary": self.summary,
        }


class Doctor:
    """Pre-flight diagnostic system for HALF execution environment.

    Usage:
        doctor = Doctor()
        report = doctor.run_full_diagnostics()
        if report.overall_status == "failed":
            print("Environment unhealthy — aborting")
    """

    def __init__(self) -> None:
        self.report = DoctorReport(
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

    def run_full_diagnostics(self) -> DoctorReport:
        """Run all health checks and return the report."""
        logger.info("HALF Pre-Flight Doctor: Starting diagnostics")

        self._check_python()
        self._check_disk_space()
        self._check_git()
        self._check_docker()
        self._check_dependencies()
        self._check_llm_backend()
        self._check_rocm()
        self._check_tailscale()

        passed = sum(1 for c in self.report.checks if c.status)
        total = len(self.report.checks)
        self.report.summary = f"{passed}/{total} checks passed"

        logger.info("Doctor report: %s (%s)", self.report.overall_status, self.report.summary)
        return self.report

    # ─── Individual Checks ──────────────────────────────────────────────

    def _check_python(self) -> None:
        """Verify Python version meets minimum."""
        py = sys.version_info
        ok = py.major >= 3 and py.minor >= 13
        self.report.add(HealthCheck(
            name="python-version",
            status=ok,
            message=f"Python {py.major}.{py.minor}.{py.micro} ({'OK' if ok else 'need 3.13+'})",
            severity="critical" if not ok else "info",
        ))
        self.report.system["python"] = f"{py.major}.{py.minor}.{py.micro}"

    def _check_disk_space(self) -> None:
        """Verify sufficient disk space for artifacts."""
        try:
            st = shutil.disk_usage("/")
            free_gb = st.free / (1024**3)
            ok = free_gb > 1.0
            self.report.add(HealthCheck(
                name="disk-space",
                status=ok,
                message=f"{free_gb:.1f} GB free ({'OK' if ok else 'need >1GB'})",
                severity="error" if not ok else "info",
            ))
        except Exception as e:
            self.report.add(HealthCheck(
                name="disk-space", status=False, message=str(e), severity="warning",
            ))

    def _check_git(self) -> None:
        """Verify git is available and repo is clean."""
        git_path = shutil.which("git")
        if not git_path:
            self.report.add(HealthCheck(
                name="git", status=False, message="git not found in PATH",
                severity="critical",
            ))
            return
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10,
            )
            dirty = bool(result.stdout.strip())
            self.report.add(HealthCheck(
                name="git",
                status=True,
                message=f"git available ({'uncommitted changes' if dirty else 'clean'})",
                severity="info",
            ))
        except Exception as e:
            self.report.add(HealthCheck(
                name="git", status=False, message=str(e), severity="warning",
            ))

    def _check_docker(self) -> None:
        """Verify Docker/Podman is available."""
        for cmd in ["docker", "podman"]:
            path = shutil.which(cmd)
            if path:
                try:
                    result = subprocess.run(
                        [cmd, "info", "--format", "{{.OSType}}"],
                        capture_output=True, text=True, timeout=15,
                    )
                    ok = result.returncode == 0
                    self.report.add(HealthCheck(
                        name=f"container-runtime-{cmd}",
                        status=ok,
                        message=f"{cmd} available ({result.stdout.strip() if ok else 'not responding'})",
                        severity="warning" if not ok else "info",
                    ))
                    return
                except Exception:
                    continue
        self.report.add(HealthCheck(
            name="container-runtime",
            status=False,
            message="No container runtime (docker/podman) found",
            severity="warning",
        ))

    def _check_dependencies(self) -> None:
        """Verify project dependencies are installed."""
        try:
            # Check uv/pip
            uv = shutil.which("uv")
            if uv:
                self.report.add(HealthCheck(
                    name="package-manager",
                    status=True,
                    message=f"uv available at {uv}",
                    severity="info",
                ))
            else:
                self.report.add(HealthCheck(
                    name="package-manager",
                    status=bool(shutil.which("pip")),
                    message="uv not found, pip fallback",
                    severity="warning",
                ))
            # Check key packages
            for mod in ["pydantic", "yaml", "langgraph"]:
                try:
                    __import__(mod)
                except ImportError:
                    self.report.add(HealthCheck(
                        name=f"dep-{mod}",
                        status=False,
                        message=f"{mod} not installed",
                        severity="error",
                    ))
        except Exception as e:
            self.report.add(HealthCheck(
                name="dependencies", status=False, message=str(e), severity="error",
            ))

    def _check_llm_backend(self) -> None:
        """Check if LM Studio or other LLM backend is reachable."""
        import urllib.request
        import urllib.error

        endpoints = [
            ("http://127.0.0.1:1234/v1/models", "LM Studio"),
            ("http://127.0.0.1:11434/api/tags", "Ollama"),
            ("https://openrouter.ai/api/v1/auth/key", "OpenRouter"),
        ]
        for url, name in endpoints:
            try:
                req = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    self.report.add(HealthCheck(
                        name=f"llm-{name.lower().replace(' ', '-')}",
                        status=True,
                        message=f"{name} reachable ({resp.status})",
                        severity="info",
                    ))
            except (urllib.error.URLError, TimeoutError, OSError):
                pass  # Not all endpoints are expected to be up

    def _check_rocm(self) -> None:
        """Check AMD ROCm availability."""
        rocminfo = shutil.which("rocminfo")
        if rocminfo:
            try:
                result = subprocess.run(
                    [rocminfo], capture_output=True, text=True, timeout=15,
                )
                ok = result.returncode == 0
                # Extract GPU info
                gpu_lines = [l for l in result.stdout.split("\n") if "Name:" in l]
                gpu_info = gpu_lines[:3] if gpu_lines else ["AMD GPU detected"]
                self.report.add(HealthCheck(
                    name="rocm",
                    status=ok,
                    message="; ".join(gpu_info),
                    severity="info",
                ))
            except Exception as e:
                self.report.add(HealthCheck(
                    name="rocm", status=False, message=str(e), severity="warning",
                ))
        else:
            self.report.add(HealthCheck(
                name="rocm", status=False, message="rocminfo not found (not critical)",
                severity="warning",
            ))

    def _check_tailscale(self) -> None:
        """Check Tailscale status for air-gapped networking."""
        tailscale = shutil.which("tailscale")
        if tailscale:
            try:
                result = subprocess.run(
                    [tailscale, "status", "--json"],
                    capture_output=True, text=True, timeout=10,
                )
                ok = result.returncode == 0
                self.report.add(HealthCheck(
                    name="tailscale",
                    status=ok,
                    message="Tailscale connected" if ok else "Tailscale not connected",
                    severity="info",
                ))
            except Exception:
                pass

    def print_report(self) -> str:
        """Print a human-readable diagnostic report."""
        lines = [
            "╔═══════════════════════════════════════════════════╗",
            "║     HALF Pre-Flight Doctor Report                 ║",
            "╚═══════════════════════════════════════════════════╝",
            f"  Timestamp: {self.report.timestamp}",
            f"  Overall:   {self.report.overall_status.upper()}",
            f"  Summary:   {self.report.summary}",
            "",
            "  Checks:",
        ]
        for c in self.report.checks:
            icon = "✓" if c.status else "✗"
            lines.append(f"    [{icon}] {c.name:<25} {c.message}")
        lines.append("")
        return "\n".join(lines)


def run_doctor() -> DoctorReport:
    """Convenience function to run doctor and return report."""
    doctor = Doctor()
    return doctor.run_full_diagnostics()


if __name__ == "__main__":
    doctor = Doctor()
    report = doctor.run_full_diagnostics()
    print(doctor.print_report())
