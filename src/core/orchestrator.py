"""
HALF — Phase Orchestrator

Manages the 5-phase lifecycle execution:
- Injects phase context into agent prompts
- Dispatches the appropriate agent skill for each phase step
- Invokes gate checks between phases
- Triggers fail-safe escalation on gate failure
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.state import StateMachineContext

logger = logging.getLogger("half.orchestrator")


class Phase(Enum):
    PHASE_1 = "phase-1"
    PHASE_2 = "phase-2"
    PHASE_3 = "phase-3"
    PHASE_4 = "phase-4"
    PHASE_5 = "phase-5"


PHASE_ORDER = [
    Phase.PHASE_1,
    Phase.PHASE_2,
    Phase.PHASE_3,
    Phase.PHASE_4,
    Phase.PHASE_5,
]

PHASE_LABELS = {
    Phase.PHASE_1: "Discovery & Strategy",
    Phase.PHASE_2: "Development & Coding",
    Phase.PHASE_3: "Quality Assurance",
    Phase.PHASE_4: "Polish & Deployment",
    Phase.PHASE_5: "Iteration",
}

PHASE_AGENTS = {
    Phase.PHASE_1: {
        "1A": "HALF-Discovery",
        "1B": "HALF-Specification",
        "1C": "HALF-Architect",
    },
    Phase.PHASE_2: {
        "2A": "HALF-Scaffold",
        "2B": "HALF-Implement",
    },
    Phase.PHASE_3: {
        "3A": "HALF-Testing",
        "3B": "HALF-Security",
        "3C": "HALF-Integration",
    },
    Phase.PHASE_4: {
        "4A": "HALF-Infrastructure",
        "4B": "HALF-CICD",
        "4C": "HALF-Launch",
    },
    Phase.PHASE_5: {
        "5A": "HALF-Observe",
        "5B": "HALF-Iterate",
        "5C": "HALF-Codify",
    },
}

PHASE_ARTIFACTS = {
    Phase.PHASE_1: [
        "01-REQUIREMENTS.md",
        "02-SPECIFICATION.md",
        "03-TASKS.md",
        "04-ARCHITECTURE.md",
        "05-ADRs.md",
    ],
    Phase.PHASE_2: ["scaffold/", "implemented-features/"],
    Phase.PHASE_3: [
        "test-quality-report.md",
        "security-scan.md",
        "red-team-report.md",
        "integration-test-report.md",
    ],
    Phase.PHASE_4: [
        "infra/",
        "rollback-plan.md",
        "production-readiness.md",
    ],
    Phase.PHASE_5: [
        "monitoring-loops.yaml",
        "triage-playbook.md",
    ],
}


class PipelineMode(Enum):
    FULL = "full"
    PROTOTYPE = "prototype"
    PATCH = "patch"
    AUDIT = "audit"


MODE_PHASES = {
    PipelineMode.FULL: [
        Phase.PHASE_1,
        Phase.PHASE_2,
        Phase.PHASE_3,
        Phase.PHASE_4,
        Phase.PHASE_5,
    ],
    PipelineMode.PROTOTYPE: [Phase.PHASE_1, Phase.PHASE_2, Phase.PHASE_4],
    PipelineMode.PATCH: [Phase.PHASE_5],
    PipelineMode.AUDIT: [Phase.PHASE_3, Phase.PHASE_5],
}


class Orchestrator:
    """Main lifecycle orchestrator for HALF.

    Manages phase execution, gate checking, and artifact tracking.
    """

    def __init__(
        self,
        project_name: str,
        mode: PipelineMode = PipelineMode.FULL,
        workspace: Path | None = None,
    ):
        self.project_name = project_name
        self.mode = mode
        self.workspace = Path(workspace) if workspace else Path.cwd() / ".hale"
        self.artifacts_dir = self.workspace / "artifacts"
        self.gates_dir = self.workspace / "gates"
        self.logs_dir = self.workspace / "logs"
        self.metrics_dir = self.workspace / "metrics"
        self.state_ctx = StateMachineContext(
            project=project_name,
            checkpoint_dir=self.workspace / "state" / "checkpoints",
        )

        # Create directory structure
        for d in [self.artifacts_dir, self.gates_dir, self.logs_dir, self.metrics_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self._phase_idx = 0
        self._active_phase: Phase | None = None
        self._completed_phases: list[Phase] = []

    @property
    def active_phase(self) -> Phase | None:
        return self._active_phase

    @property
    def active_phases(self) -> list[Phase]:
        """Return the ordered list of phases active for the current mode."""
        return MODE_PHASES[self.mode]

    @property
    def completed_phases(self) -> list[Phase]:
        return list(self._completed_phases)

    def next_phase(self) -> Phase | None:
        """Advance to the next phase in the pipeline.

        Returns:
            The next Phase to execute, or None if pipeline is complete.
        """
        phases = self.active_phases

        if self._phase_idx >= len(phases):
            logger.info("All phases completed for mode %s", self.mode.value)
            return None

        self._active_phase = phases[self._phase_idx]
        self.state_ctx.transition_to_phase(self._active_phase.value)
        logger.info(
            "Advancing to %s: %s",
            self._active_phase.value,
            PHASE_LABELS[self._active_phase],
        )
        return self._active_phase

    def complete_phase(self) -> None:
        """Mark the current phase as completed and advance."""
        if self._active_phase:
            self._completed_phases.append(self._active_phase)
            self._phase_idx += 1

    def get_phase_artifacts(self, phase: Phase) -> list[str]:
        """Get the expected artifacts for a given phase."""
        return PHASE_ARTIFACTS.get(phase, [])

    def get_phase_agents(self, phase: Phase) -> dict[str, str]:
        """Get the agent skills for a given phase."""
        return PHASE_AGENTS.get(phase, {})

    def log_gate_result(
        self,
        gate_id: str,
        passed: bool,
        details: dict[str, Any],
    ) -> Path:
        """Log a gate check result to the gates directory."""
        result = {
            "gate_id": gate_id,
            "phase": self._active_phase.value if self._active_phase else None,
            "project": self.project_name,
            "passed": passed,
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "details": details,
        }
        log_path = (
            self.gates_dir
            / f"{gate_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        log_path.write_text(json.dumps(result, indent=2))
        logger.info("Gate %s: %s", gate_id, "PASSED" if passed else "FAILED")
        return log_path

    def get_pipeline_status(self) -> dict[str, Any]:
        """Get current pipeline status summary."""
        return {
            "project": self.project_name,
            "mode": self.mode.value,
            "active_phase": self._active_phase.value if self._active_phase else None,
            "completed_phases": [p.value for p in self._completed_phases],
            "pending_phases": [
                p.value
                for p in self.active_phases
                if p not in self._completed_phases and p != self._active_phase
            ],
            "workspace": str(self.workspace),
        }

    def generate_gap_report(
        self,
        gate_id: str,
        failures: list[dict[str, Any]],
        attempts: int = 0,
    ) -> dict[str, Any]:
        """Generate a structured gap report when auto-remediation fails.

        Args:
            gate_id: The gate check that failed.
            failures: List of failure details.
            attempts: Number of retry attempts made.

        Returns:
            Gap report data structure for template rendering.
        """
        return {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "phase": self._active_phase.value if self._active_phase else "unknown",
            "gate_id": gate_id,
            "project": self.project_name,
            "description": f"Gate {gate_id} failed after {attempts} retries",
            "what_was_tried": [
                {
                    "attempt": i + 1,
                    "timestamp": datetime.now(tz=UTC).isoformat(),
                    "approach": "auto-remediation",
                    "result": f"Failed: {f.get('details', 'unknown')}",
                }
                for i, f in enumerate(failures)
            ],
            "current_state": {
                "completed_phases": [p.value for p in self._completed_phases],
                "pending_phases": [
                    p.value
                    for p in self.active_phases
                    if p not in self._completed_phases
                ],
                "retries_used": attempts,
            },
        }
