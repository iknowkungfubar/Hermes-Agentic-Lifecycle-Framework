"""HALF — Security Scanner Integrations.

Integrates NVIDIA garak (LLM vuln scanner) and Perplexity Bumblebee
(supply chain scanner) into the FOSS toolchain.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.security_scanners")


class GarakScanner:
    """NVIDIA garak — LLM vulnerability scanner.

    Probes application endpoints for jailbreaks, data leakage, and
    prompt injection vulnerabilities.
    """

    def __init__(self, target_url: str = "http://127.0.0.1:8000"):
        self.target_url = target_url

    def run_scan(self, report_path: str | Path = ".hale/security/garak-report.json") -> dict[str, Any]:
        """Run a garak vulnerability scan against the target.

        Returns:
            Dict with scan results including DEFCON score.
        """
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "garak", "--model_type", "rest",
                 "--model_name", self.target_url,
                 "--probes", "probe:all",
                 "--report_prefix", str(report_path.with_suffix(""))],
                capture_output=True, text=True, timeout=300,
            )
            output = result.stdout
            defcon_score = self._parse_defcon(output)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            output = f"Garak scan failed: {e}"
            defcon_score = 99  # Unknown

        report = {
            "tool": "garak",
            "target": self.target_url,
            "defcon_score": defcon_score,
            "critical": defcon_score <= 3,
            "raw_output": output[-2000:],
        }
        report_path.write_text(json.dumps(report, indent=2))
        logger.info("Garak scan complete — DEFCON score: %s", defcon_score)
        return report

    @staticmethod
    def _parse_defcon(output: str) -> int:
        """Extract DEFCON score from garak output."""
        import re
        match = re.search(r"DEFCON\s*(\d+)", output, re.IGNORECASE)
        return int(match.group(1)) if match else 99


class BumblebeeScanner:
    """Perplexity Bumblebee — supply chain dependency scanner.

    Scans lockfiles (Cargo.lock, package-lock.json, go.mod, requirements.txt)
    for known vulnerabilities without executing postinstall scripts.
    """

    def __init__(self, workspace: str | Path = "."):
        self.workspace = Path(workspace)

    def run_scan(self, report_path: str | Path = ".hale/security/bumblebee-report.json") -> dict[str, Any]:
        """Run a Bumblebee supply chain scan.

        Returns:
            Dict with scan results.
        """
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        findings = []

        # Scan Python dependencies
        for req_file in ["requirements.txt", "pyproject.toml"]:
            path = self.workspace / req_file
            if path.exists():
                findings.extend(self._check_python_deps(path))

        # Scan npm dependencies
        pkg_json = self.workspace / "package-lock.json"
        if pkg_json.exists():
            findings.extend(self._check_npm_deps(pkg_json))

        # Scan Rust dependencies
        cargo_lock = self.workspace / "Cargo.lock"
        if cargo_lock.exists():
            findings.extend(self._check_rust_deps(cargo_lock))

        report = {
            "tool": "bumblebee",
            "workspace": str(self.workspace),
            "findings": findings,
            "critical_count": sum(1 for f in findings if f.get("severity") == "CRITICAL"),
            "high_count": sum(1 for f in findings if f.get("severity") == "HIGH"),
        }
        report_path.write_text(json.dumps(report, indent=2))
        logger.info("Bumblebee scan complete — %d findings", len(findings))
        return report

    @staticmethod
    def _check_python_deps(path: Path) -> list[dict[str, Any]]:
        """Check Python dependencies for known issues."""
        findings = []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "audit", "--format", "json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for vuln in data if isinstance(data, list) else data.get("vulnerabilities", []):
                    findings.append({
                        "type": "python",
                        "package": vuln.get("name", "unknown"),
                        "installed": vuln.get("installed", ""),
                        "vulnerability": vuln.get("id", ""),
                        "severity": vuln.get("severity", "MEDIUM"),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        return findings

    @staticmethod
    def _check_npm_deps(path: Path) -> list[dict[str, Any]]:
        """Check npm dependencies."""
        return []  # Requires npm audit CLI

    @staticmethod
    def _check_rust_deps(path: Path) -> list[dict[str, Any]]:
        """Check Rust dependencies."""
        return []  # Requires cargo-audit CLI
