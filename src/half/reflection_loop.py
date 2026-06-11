"""HALF — Reflection Loop: Weekly Offline Review Agent.

A scheduled agent that executes weekly over the repository's commit history
and telemetry logs. It analyzes pattern failures in the validation loop and
autonomously suggests updates for global rules in the MentorScripts or
proposes new tools for .harness/skills/.

Based on the HALF doctrine's Phase 5 'Continuous System Evolution' spec.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.reflection_loop")


@dataclass
class ReflectionFinding:
    """A finding from the reflection analysis."""

    category: str  # pattern_failure, mentor_update, skill_proposal, test_gap
    description: str
    evidence: str  # Supporting data from logs/commits
    suggested_change: str  # What to update
    priority: str = "medium"  # high, medium, low


@dataclass
class ReflectionReport:
    """Weekly reflection report."""

    week_start: str
    week_end: str
    findings: list[ReflectionFinding] = field(default_factory=list)
    summary: str = ""
    pr_branch: str = ""
    pr_created: bool = False


class ReflectionLoop:
    """Weekly offline review of agent performance and system evolution.

    Analyzes:
    - Commit history for repeated error patterns
    - Test failures for flaky or missing tests
    - CI/CD logs for pipeline bottlenecks
    - Laminar telemetry for agent performance (if available)

    Generates:
    - Updated MentorScript rules
    - New .harness/skills/ proposals
    - Pull requests with auto-generated improvements
    """

    def __init__(self, repo_path: str | Path = "."):
        self.repo_path = Path(repo_path)
        now = datetime.now(tz=timezone.utc)
        week_ago = now - timedelta(days=7)
        self.report = ReflectionReport(
            week_start=week_ago.isoformat(),
            week_end=now.isoformat(),
        )

    def run(self) -> ReflectionReport:
        """Execute the weekly reflection analysis.

        Returns:
            ReflectionReport with findings and suggestions.
        """
        logger.info("Reflection Loop: Starting weekly analysis")

        self._analyze_commit_history()
        self._analyze_test_failures()
        self._analyze_mentor_effectiveness()
        self._propose_skill_improvements()
        self._create_pr()

        self.report.summary = (
            f"Reflection Loop: {len(self.report.findings)} findings, "
            f"PR: {'created' if self.report.pr_created else 'skipped'}"
        )
        logger.info(self.report.summary)
        return self.report

    def _analyze_commit_history(self) -> None:
        """Scan commit messages for repeated fix patterns indicating root issues."""
        try:
            result = subprocess.run(
                ["git", "log", "--since=7.days", "--oneline"],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )
            commits = result.stdout.strip().split("\n")
            if not commits or commits == [""]:
                logger.info("Reflection Loop: No commits in the last week")
                return

            # Look for patterns indicating systemic issues
            fix_commits = [c for c in commits if "fix" in c.lower()]
            if len(fix_commits) > len(commits) * 0.5:
                self.report.findings.append(ReflectionFinding(
                    category="pattern_failure",
                    description=f"{len(fix_commits)}/{len(commits)} commits are fixes — possible systemic quality issue",
                    evidence="\n".join(fix_commits[:5]),
                    suggested_change="Review root causes — consider adding pre-commit checks or stricter gates",
                    priority="high",
                ))

            # Check for repeated security fixes
            security_commits = [c for c in commits if any(kw in c.lower()
                                for kw in ["security", "cve", "vuln", "xs", "inject"])]
            if len(security_commits) >= 3:
                self.report.findings.append(ReflectionFinding(
                    category="pattern_failure",
                    description=f"{len(security_commits)} security-related commits in one week",
                    evidence="\n".join(security_commits[:5]),
                    suggested_change="Add security scanning to CI pipeline and security.md rules to MentorScript",
                    priority="high",
                ))

            # Check for "fix fix" patterns (repeated fixes on same area)
            areas: dict[str, int] = {}
            for c in commits:
                for part in c.split(":")[1:]:
                    words = part.strip().split()
                    if words:
                        areas[words[0]] = areas.get(words[0], 0) + 1
            hot_areas = {k: v for k, v in areas.items() if v >= 3}
            if hot_areas:
                for area, count in hot_areas.items():
                    self.report.findings.append(ReflectionFinding(
                        category="pattern_failure",
                        description=f"Hotspot: '{area}' modified {count} times in week ({count}/day avg)",
                        evidence=f"Area {area} has {count} commits",
                        suggested_change=f"Consider refactoring or adding tests for {area}",
                        priority="medium",
                    ))

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("Reflection Loop: Git analysis failed: %s", e)

    def _analyze_test_failures(self) -> None:
        """Analyze pytest results for flaky or consistently failing tests."""
        try:
            # Run tests and capture failures
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "-q", "--tb=line", "--json-report"],
                capture_output=True, text=True, timeout=120,
                cwd=str(self.repo_path),
            )

            # Try to parse json report
            report_file = self.repo_path / ".pytest_cache" / ".reports" / "report.json"
            if report_file.exists():
                try:
                    data = json.loads(report_file.read_text())
                    failures = data.get("failures", [])
                    if failures:
                        self.report.findings.append(ReflectionFinding(
                            category="test_gap",
                            description=f"{len(failures)} test(s) failing in latest run",
                            evidence="\n".join(f.get("call", {}).get("longrepr", "")[:100]
                                               for f in failures[:3]),
                            suggested_change="Fix failing tests or mark as expected failures with xfail",
                            priority="high" if len(failures) > 3 else "medium",
                        ))
                except (json.JSONDecodeError, KeyError):
                    pass

            # Check for flaky tests by running a subset twice
            if result.returncode != 0:
                flaky_check = subprocess.run(
                    ["python3", "-m", "pytest", "tests/", "-q", "--tb=line", "-x"],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(self.repo_path),
                )
                if flaky_check.returncode == 0 and result.returncode != 0:
                    self.report.findings.append(ReflectionFinding(
                        category="test_gap",
                        description="Possible flaky tests — test suite passes on retry",
                        evidence="First run failed, second run passed",
                        suggested_change="Tag flaky tests with @pytest.mark.flaky and investigate",
                        priority="medium",
                    ))

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("Reflection Loop: Test analysis failed: %s", e)

    def _analyze_mentor_effectiveness(self) -> None:
        """Check if the current MentorScript rules are effective.

        Analyzes whether AGENTS.md needs updates based on recent errors.
        """
        agents_file = self.repo_path / ".harness" / "agents.md"
        if not agents_file.exists():
            self.report.findings.append(ReflectionFinding(
                category="mentor_update",
                description="MentorScript (.harness/agents.md) not found",
                evidence="File missing from .harness/ directory",
                suggested_change="Create .harness/agents.md with project conventions and routing rules",
                priority="medium",
            ))
            return

        # Check if mentor is stale (>30 days since last commit)
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", "--", ".harness/agents.md"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )
            if result.stdout:
                try:
                    last_modified = datetime.strptime(
                        result.stdout.strip(), "%Y-%m-%d %H:%M:%S %z"
                    )
                    age = (datetime.now(tz=timezone.utc) - last_modified).days
                    if age > 30:
                        self.report.findings.append(ReflectionFinding(
                            category="mentor_update",
                            description=f"MentorScript not updated in {age} days",
                            evidence=f"Last modified: {result.stdout.strip()}",
                            suggested_change="Review and update MentorScript rules based on recent project changes",
                            priority="low",
                        ))
                except ValueError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _propose_skill_improvements(self) -> None:
        """Propose new skills for .harness/skills/ based on observed needs."""
        # Check if there are skills already
        skills_dir = self.repo_path / ".harness" / "skills"
        if not skills_dir.exists():
            self.report.findings.append(ReflectionFinding(
                category="skill_proposal",
                description="No Portable Skill Modules found in .harness/skills/",
                evidence="Skills directory is empty or missing",
                suggested_change="Add standard skills: browser-use for web research, data-analysis for CSV/Excel processing",
                priority="low",
            ))
            return

        existing = list(skills_dir.glob("*"))
        if len(existing) < 3:
            self.report.findings.append(ReflectionFinding(
                category="skill_proposal",
                description=f"Only {len(existing)} skill(s) in .harness/skills/ — consider expanding",
                evidence=f"Found: {', '.join(f.name for f in existing)}",
                suggested_change="Add commonly needed skills: browser-use, financial-data, legal-document-generation",
                priority="low",
            ))

    def _create_pr(self) -> None:
        """Create a Git branch and PR with the reflection suggestions."""
        if not self.report.findings:
            logger.info("Reflection Loop: No findings — skipping PR creation")
            return

        branch_name = f"reflection/weekly-{datetime.now(tz=timezone.utc).strftime('%Y%m%d')}"
        self.report.pr_branch = branch_name

        try:
            # Create branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )

            # Write report to artifacts
            report_path = self.repo_path / ".hale" / "artifacts" / "phase-5" / f"reflection-{datetime.now(tz=timezone.utc).strftime('%Y%m%d')}.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(self._generate_report_markdown())

            # Try to update MentorScript if suggested
            for finding in self.report.findings:
                if finding.category == "mentor_update" and finding.priority == "high":
                    agents_file = self.repo_path / ".harness" / "agents.md"
                    if agents_file.exists():
                        agents_file.write_text(
                            agents_file.read_text() + f"\n# Reflection Loop Update ({datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')})\n# {finding.suggested_change}\n"
                        )

            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )
            subprocess.run(
                ["git", "commit", "-m", f"reflection: weekly review — {len(self.report.findings)} findings"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )
            subprocess.run(
                ["git", "checkout", "-"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )

            self.report.pr_created = True
            logger.info("Reflection Loop: Created branch %s", branch_name)

        except Exception as e:
            logger.warning("Reflection Loop: PR creation failed: %s", e)

    def _generate_report_markdown(self) -> str:
        """Generate the weekly reflection report as markdown.

        Returns:
            Markdown report string.
        """
        lines = [
            f"# Reflection Loop Report — {self.report.week_start[:10]} to {self.report.week_end[:10]}",
            "",
            f"**Total findings:** {len(self.report.findings)}",
            "",
        ]

        for category in ["pattern_failure", "test_gap", "mentor_update", "skill_proposal"]:
            cat_findings = [f for f in self.report.findings if f.category == category]
            if not cat_findings:
                continue

            cat_name = category.replace("_", " ").title()
            lines.append(f"## {cat_name}")
            for f in cat_findings:
                icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(f.priority, "⚪")
                lines.extend([
                    f"### {icon} [{f.priority}] {f.description}",
                    f"- **Evidence:** {f.evidence}",
                    f"- **Suggested change:** {f.suggested_change}",
                    "",
                ])

        return "\n".join(lines)
