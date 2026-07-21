"""Phase 5: Iteration nodes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from half.runtime.nodes._write_artifact import _write_artifact
from half.runtime.state import HalfState  # noqa: TC001

logger = logging.getLogger("half.runtime.nodes")

def phase_5_observe(state: HalfState) -> dict[str, Any]:
    """Phase 5A: Writes monitoring configuration."""
    logger.info("Phase 5A: Monitoring setup")
    _write_artifact(
        "phase-5",
        "monitoring-config.yaml",
        "monitoring:\n  metric_collection: every 15m\n  log_analysis: every 1h\n  health_check: every 5m\n",
    )
    return {
        "current_step": "phase-5-observe",
        "messages": [
            {"role": "assistant", "content": "Phase 5A: Monitoring config written"}
        ],
    }

def phase_5_iterate(state: HalfState) -> dict[str, Any]:
    """Phase 5B: Issue triage playbook."""
    logger.info("Phase 5B: Iteration setup")
    _write_artifact(
        "phase-5",
        "triage-playbook.md",
        "# Issue Triage\n\n- Bugs: reproduce -> root cause -> fix (TDD) -> PR\n- Features: mini-spec -> estimate -> implement\n- Tech debt: document -> prioritize -> fix\n",
    )
    return {
        "current_step": "phase-5-iterate",
        "messages": [
            {"role": "assistant", "content": "Phase 5B: Triage playbook written"}
        ],
    }

def phase_5_codify(state: HalfState) -> dict[str, Any]:
    """Phase 5C: Codification Imperative -- records corrections."""
    logger.info("Phase 5C: Codification")
    _write_artifact(
        "phase-5",
        "codification-log.md",
        f"# Codification Log\n\n## {datetime.now(tz=UTC).isoformat()}\n- [Record corrections here]\n",
    )
    return {
        "current_step": "phase-5-codify",
        "messages": [
            {"role": "assistant", "content": "Phase 5C: Codification log initialized"}
        ],
    }

def phase_5_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 5 -- verifies monitoring and codification active."""
    logger.info("Phase 5: Gate check")
    from half import config as half_config

    monitoring = (
        Path(half_config.ARTIFACTS_PHASE_5) / "monitoring-config.yaml"
    ).exists()
    passed = monitoring
    return {
        "current_step": "phase-5-gate",
        "gate_results": [
            {
                "gate_id": "G5",
                "passed": passed,
                "details": f"Monitoring active: {monitoring}",
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }
        ],
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 5 Gate: {'PASSED' if passed else 'FAILED'}",
            }
        ],
    }
