"""
HALF — Artifact Manager

Handles lifecycle artifacts: creation, validation, and cross-referencing
between phases.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger("half.artifacts")


class ArtifactManager:
    """Manages HALF artifacts across all phases.

    Provides structure validation, cross-phase dependency checking,
    and artifact lifecycle methods.
    """

    REQUIRED_ARTIFACTS = {
        "phase-1": [
            "01-REQUIREMENTS.md",
            "02-SPECIFICATION.md",
            "03-TASKS.md",
            "04-ARCHITECTURE.md",
            "05-ADRs.md",
        ],
        "phase-2": [],
        "phase-3": [
            "test-quality-report.md",
            "security-scan.md",
            "red-team-report.md",
            "integration-test-report.md",
        ],
        "phase-4": [
            "rollback-plan.md",
            "production-readiness.md",
        ],
        "phase-5": [
            "monitoring-loops.yaml",
            "triage-playbook.md",
        ],
    }

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir  # .hale/artifacts/
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def ensure_phase_dir(self, phase: str) -> Path:
        """Create and return the directory for a phase's artifacts."""
        phase_dir = self.base_dir / phase
        phase_dir.mkdir(parents=True, exist_ok=True)
        return phase_dir

    def write_artifact(
        self,
        phase: str,
        filename: str,
        content: str,
    ) -> Path:
        """Write an artifact file for a given phase.

        Args:
            phase: Phase name (e.g., 'phase-1').
            filename: Artifact filename (e.g., '01-REQUIREMENTS.md').
            content: File content.

        Returns:
            Path to the written artifact.
        """
        phase_dir = self.ensure_phase_dir(phase)
        filepath = phase_dir / filename
        filepath.write_text(content)
        logger.info("Written artifact: %s", filepath)
        return filepath

    def read_artifact(self, phase: str, filename: str) -> str | None:
        """Read an artifact file if it exists.

        Args:
            phase: Phase name.
            filename: Artifact filename.

        Returns:
            File content or None if not found.
        """
        filepath = self.base_dir / phase / filename
        if filepath.exists():
            return filepath.read_text()
        return None

    def verify_phase_artifacts(self, phase: str) -> dict[str, bool]:
        """Verify that all required artifacts for a phase exist.

        Args:
            phase: Phase name to verify.

        Returns:
            Dict mapping artifact names to existence (True/False).
        """
        required = self.REQUIRED_ARTIFACTS.get(phase, [])
        phase_dir = self.base_dir / phase
        return {name: (phase_dir / name).exists() for name in required}

    def all_phases_complete(self) -> dict[str, bool]:
        """Check artifact completeness across all phases.

        Returns:
            Dict mapping phase names to completeness (all artifacts present).
        """
        return {
            phase: all(self.verify_phase_artifacts(phase).values())
            for phase in self.REQUIRED_ARTIFACTS
        }

    def list_artifacts(self, phase: str | None = None) -> list[Path]:
        """List all artifact files, optionally filtered by phase.

        Args:
            phase: Optional phase filter.

        Returns:
            List of artifact file paths.
        """
        if phase:
            phase_dir = self.base_dir / phase
            if phase_dir.exists():
                return sorted(phase_dir.iterdir())
            return []
        artifacts: list[Path] = []
        for phase_dir in sorted(self.base_dir.iterdir()):
            if phase_dir.is_dir():
                artifacts.extend(sorted(phase_dir.iterdir()))
        return artifacts

    def get_phase_summary(self, phase: str) -> dict[str, object]:
        """Get a summary of artifacts in a phase.

        Args:
            phase: Phase name.

        Returns:
            Dict with phase info and artifact details.
        """
        phase_dir = self.base_dir / phase
        if not phase_dir.exists():
            return {"phase": phase, "exists": False, "artifacts": []}

        artifacts = []
        for f in sorted(phase_dir.iterdir()):
            if f.is_file():
                artifacts.append(
                    {
                        "name": f.name,
                        "size": f.stat().st_size,
                        "lines": len(f.read_text().splitlines())
                        if f.suffix in {".md", ".yaml", ".yml", ".json", ".py"}
                        else 0,
                    }
                )

        return {
            "phase": phase,
            "exists": True,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        }
