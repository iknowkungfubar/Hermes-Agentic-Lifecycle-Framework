"""
HALF-Launch Agent (Phase 4C)

Production readiness verification and rollback plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReadinessCheck:
    """A single production readiness checklist item."""

    id: str
    description: str
    checked: bool = False
    category: str = "general"


READINESS_CHECKS: list[ReadinessCheck] = [
    ReadinessCheck("PR-01", "All CI checks pass on main branch", category="ci"),
    ReadinessCheck(
        "PR-02", "Docker image built and pushed to registry", category="build"
    ),
    ReadinessCheck(
        "PR-03",
        "Database migrations validated (dry-run against staging)",
        category="database",
    ),
    ReadinessCheck("PR-04", "Rollback plan documented", category="operations"),
    ReadinessCheck(
        "PR-05", "Monitoring dashboards configured", category="observability"
    ),
    ReadinessCheck(
        "PR-06", "Alert thresholds defined (P1/P2/P3)", category="observability"
    ),
    ReadinessCheck(
        "PR-07",
        "Health check endpoints operational (/health, /ready, /metrics)",
        category="infra",
    ),
    ReadinessCheck(
        "PR-08",
        "Backup strategy implemented (database + file storage)",
        category="operations",
    ),
    ReadinessCheck(
        "PR-09",
        "Secret management verified (no hardcoded secrets)",
        category="security",
    ),
    ReadinessCheck("PR-10", "Rate limiting configured and tested", category="security"),
    ReadinessCheck(
        "PR-11",
        "CORS configuration correct (production origins whitelisted)",
        category="security",
    ),
    ReadinessCheck(
        "PR-12", "SSL/TLS termination configured (certificates valid)", category="infra"
    ),
    ReadinessCheck(
        "PR-13", "Error tracking service configured", category="observability"
    ),
    ReadinessCheck(
        "PR-14",
        "Log aggregation configured (structured JSON logs)",
        category="observability",
    ),
    ReadinessCheck(
        "PR-15",
        "Dependency licenses verified (no GPL/AGPL conflicts)",
        category="compliance",
    ),
    ReadinessCheck(
        "PR-16", "Feature flags configured (if gradual rollout)", category="operations"
    ),
    ReadinessCheck(
        "PR-17", "Stakeholders notified of release window", category="process"
    ),
    ReadinessCheck(
        "PR-18", "Runbook created for first-week operations", category="operations"
    ),
]


class LaunchAgent:
    """Phase 4C: Production readiness verification."""

    def __init__(self):
        self.checks: dict[str, ReadinessCheck] = {c.id: c for c in READINESS_CHECKS}

    def mark_complete(self, check_id: str) -> None:
        """Mark a readiness check as completed."""
        if check_id in self.checks:
            self.checks[check_id].checked = True

    def all_complete(self) -> bool:
        """Check if all readiness checks are complete."""
        return all(c.checked for c in self.checks.values())

    def completion_pct(self) -> float:
        """Calculate completion percentage."""
        if not self.checks:
            return 100.0
        completed = sum(1 for c in self.checks.values() if c.checked)
        return (completed / len(self.checks)) * 100

    def render_readiness_markdown(self) -> str:
        """Render the production readiness checklist as markdown."""
        lines = [
            "# Production Readiness Checklist",
            "",
            f"**Completion: {self.completion_pct():.0f}%**",
            "",
            "## Status",
            "",
        ]

        # Group by category
        categories: dict[str, list[ReadinessCheck]] = {}
        for c in self.checks.values():
            categories.setdefault(c.category, []).append(c)

        for category, items in sorted(categories.items()):
            lines.extend(
                [
                    f"### {category.capitalize()}",
                    "",
                    "| ID | Check | Status |",
                    "|----|-------|--------|",
                ]
            )
            for item in items:
                status = "✓" if item.checked else "□"
                lines.append(f"| {item.id} | {item.description} | {status} |")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def render_rollback_plan(
        project_name: str,
        version: str = "v1.0.0",
    ) -> str:
        """Generate a rollback plan document."""
        return f"""\
# Rollback Plan: {project_name} {version}

## One-Line Rollback
docker compose down && docker compose -f docker-compose.previous.yml up -d

## Rollback Trigger Conditions
- Error rate > 5% for 5 minutes
- p95 latency > 2x baseline for 10 minutes
- Any P1 incident reported within 1 hour of deployment
- Database migration fails → restore from backup (not rollback migration)

## Rollback Procedure
1. Identify rollback point: `docker tag app:{{previous-sha}} app:latest`
2. Execute: `docker compose down && docker compose up -d`
3. Verify health: `curl -f http://localhost:8000/health`
4. Run smoke tests: `pytest tests/smoke/`
5. Verify metrics returning to baseline

## Database Rollback Strategy
- **Migration rollback:** `alembic downgrade -1` (only if reversible)
- **Data restore:** pg_restore -d app backup.dump (if irreversible)

## Communication
- Slack: #incidents — notify on rollback start and completion
- Status page: update if user-facing
- Post-mortem scheduled within 24 hours
"""
