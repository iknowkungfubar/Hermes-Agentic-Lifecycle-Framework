"""
HALF-Security Agent (Phase 3B)

Automated security scanning and adversarial red-teaming.
Runs SAST tools, dependency audits, and spawns parallel red-team agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SecurityFinding:
    """A security finding from scanning or red-teaming."""

    id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str  # sast, dependency, secret, red-team
    file_path: str
    line_number: int
    description: str
    remediation: str
    auto_fixable: bool = False


@dataclass
class SecurityReport:
    """Complete security assessment report."""

    scan_findings: list[SecurityFinding] = field(default_factory=list)
    red_team_findings: list[SecurityFinding] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    auto_fixed_count: int = 0


class SecurityAgent:
    """Phase 3B: Security scanning and red-teaming orchestration."""

    RED_TEAM_PROFILES = {
        "pentester": (
            "You are a web application penetration tester. "
            "Audit for: SQL injection, XSS, CSRF, SSRF, IDOR, "
            "authentication bypass, privilege escalation, race conditions, "
            "and insecure deserialization."
        ),
        "cryptographer": (
            "You are a cryptography and auth specialist. "
            "Audit: password hashing (bcrypt cost), JWT signing algorithm, "
            "session management, token expiry, refresh token rotation, "
            "rate limiting bypass, OAuth misconfiguration, API key storage."
        ),
        "infrastructure": (
            "You are an infrastructure security engineer. "
            "Audit: Dockerfile (root user, exposed ports), CI/CD pipeline "
            "(secret leakage), .env file handling, CORS configuration, "
            "error message verbosity (info leakage), dependency supply chain risks."
        ),
        "ai_model": (
            "You are an AI/ML security specialist. "
            "Audit: prompt injection surfaces, output validation, "
            "data poisoning risks, model access controls, "
            "training data provenance."
        ),
    }

    def __init__(self) -> None:
        self.findings: list[SecurityFinding] = []
        self.auto_fixed: list[str] = []

    def add_finding(
        self,
        severity: str,
        category: str,
        file_path: str,
        line_number: int,
        description: str,
        remediation: str,
        auto_fixable: bool = False,
    ) -> SecurityFinding:
        """Add a security finding."""
        finding_id = f"SEC-{len(self.findings) + 1:04d}"
        finding = SecurityFinding(
            id=finding_id,
            severity=severity.upper(),
            category=category,
            file_path=file_path,
            line_number=line_number,
            description=description,
            remediation=remediation,
            auto_fixable=auto_fixable,
        )
        self.findings.append(finding)
        return finding

    def get_report(self) -> SecurityReport:
        """Compile all findings into a report."""
        report = SecurityReport()
        for f in self.findings:
            if f.category == "red-team":
                report.red_team_findings.append(f)
            else:
                report.scan_findings.append(f)

            if f.severity == "CRITICAL":
                report.critical_count += 1
            elif f.severity == "HIGH":
                report.high_count += 1
            elif f.severity == "MEDIUM":
                report.medium_count += 1
            elif f.severity == "LOW":
                report.low_count += 1

            if f.auto_fixable:
                report.auto_fixed_count += 1

        return report

    def rank_findings(self) -> list[SecurityFinding]:
        """Return findings sorted by severity."""
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        return sorted(
            self.findings,
            key=lambda f: severity_order.get(f.severity, 99),
        )

    def get_fixable_critical(self) -> list[SecurityFinding]:
        """Get CRITICAL/HIGH findings that can be auto-fixed."""
        return [
            f
            for f in self.findings
            if f.severity in ("CRITICAL", "HIGH") and f.auto_fixable
        ]

    def render_report_markdown(self, report: SecurityReport) -> str:
        """Render the security report as markdown."""
        lines = [
            "# Security Assessment Report",
            "",
            "## Summary",
            "",
            "| Metric | Count |",
            "|--------|-------|",
            f"| CRITICAL | {report.critical_count} |",
            f"| HIGH | {report.high_count} |",
            f"| MEDIUM | {report.medium_count} |",
            f"| LOW | {report.low_count} |",
            f"| Auto-Fixed | {report.auto_fixed_count} |",
            "",
            "## SAST Scan Findings",
            "",
        ]

        scan = report.scan_findings
        if not scan:
            lines.append("No SAST findings.")
        else:
            lines.append("| ID | Severity | File | Line | Description | Remediation |")
            lines.append("|----|----------|------|------|-------------|-------------|")
            for f in scan:
                lines.append(
                    f"| {f.id} | {f.severity} | {f.file_path} | {f.line_number} | "
                    f"{f.description} | {f.remediation} |"
                )

        lines.extend(
            [
                "",
                "## Red-Team Findings",
                "",
            ]
        )

        rt = report.red_team_findings
        if not rt:
            lines.append("No red-team findings.")
        else:
            lines.append("| ID | Severity | Category | Description | Remediation |")
            lines.append("|----|----------|----------|-------------|-------------|")
            for f in rt:
                lines.append(
                    f"| {f.id} | {f.severity} | {f.category} | "
                    f"{f.description} | {f.remediation} |"
                )

        lines.extend(
            [
                "",
                "## Gate Status",
                "",
                f"- **CRITICAL check:** {'PASS' if report.critical_count == 0 else 'FAIL'}",
                f"- **HIGH check:** {'PASS' if report.high_count == 0 else 'REQUIRES REVIEW'}",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def get_red_team_prompt(profile: str) -> str:
        """Get the red-teaming prompt for a specific profile."""
        return SecurityAgent.RED_TEAM_PROFILES.get(
            profile,
            "You are a security auditor. Review the codebase for vulnerabilities.",
        )
