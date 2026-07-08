"""Phase 4: Polish & Deployment nodes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from half.runtime.nodes._write_artifact import _write_artifact

if TYPE_CHECKING:
    from half.runtime.state import HalfState

logger = logging.getLogger("half.runtime.nodes")


def phase_4_infrastructure(state: HalfState) -> dict[str, Any]:
    """Phase 4A: Infrastructure as Code generation."""
    logger.info("Phase 4A: Infrastructure generation")
    _write_artifact(
        "phase-4",
        "docker-compose.yml",
        "version: '3.8'\nservices:\n  app:\n    build: .\n    ports: ['8000:8000']\n",
    )
    _write_artifact(
        "phase-4",
        "Dockerfile",
        "FROM python:3.13-slim\nWORKDIR /app\nCOPY . .\nCMD ['python', 'main.py']\n",
    )
    return {
        "current_step": "phase-4-infrastructure",
        "messages": [
            {"role": "assistant", "content": "Phase 4A: Docker config generated"}
        ],
    }


def phase_4_cicd(state: HalfState) -> dict[str, Any]:
    """Phase 4B: CI/CD pipeline generation."""
    logger.info("Phase 4B: CI/CD generation")
    _write_artifact(
        "phase-4",
        ".github/workflows/ci.yml",
        "name: CI\non: [pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install pytest && pytest\n",
    )
    return {
        "current_step": "phase-4-cicd",
        "messages": [
            {"role": "assistant", "content": "Phase 4B: CI pipeline generated"}
        ],
    }


def phase_4_launch(state: HalfState) -> dict[str, Any]:
    """Phase 4C: Production readiness checklist."""
    logger.info("Phase 4C: Launch readiness")
    checks = [
        "All CI checks pass on main branch",
        "Docker image built and pushed",
        "Database migrations validated",
        "Rollback plan documented",
        "Monitoring dashboards configured",
        "Health endpoint operational",
        "Secret management verified",
    ]
    _write_artifact(
        "phase-4",
        "production-readiness.md",
        "# Production Readiness\n\n" + "\n".join(f"- [ ] {c}" for c in checks),
    )
    _write_artifact(
        "phase-4",
        "rollback-plan.md",
        "# Rollback Plan\n\n## One-Line Rollback\n`docker compose down && docker compose up -d`\n",
    )
    return {
        "current_step": "phase-4-launch",
        "mrp_generated": True,
        "messages": [
            {
                "role": "assistant",
                "content": "Phase 4C: MRP generated -- Finality Gate ready",
            }
        ],
    }


def phase_4_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 4 -- Finality Gate check."""
    logger.info("Phase 4: Finality Gate")
    approved = state.get("deployment_approved", False)
    return {
        "current_step": "phase-4-gate",
        "gate_results": [
            {
                "gate_id": "G4",
                "passed": approved,
                "details": "Awaiting human sign-off"
                if not approved
                else "Deployment approved",
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }
        ],
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 4 Gate: {'APPROVED' if approved else 'WAITING for sign-off'}",
            }
        ],
    }
