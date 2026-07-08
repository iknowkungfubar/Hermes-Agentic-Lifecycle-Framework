"""Artifact writer utility for HALF phase nodes."""

from __future__ import annotations

import logging
from pathlib import Path

from half import config

logger = logging.getLogger("half.runtime.nodes")


def _write_artifact(phase: str, name: str, content: str) -> Path:
    """Write an artifact file and return its path."""
    phase_dir = Path(config.ARTIFACTS_DIR) / phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    path = phase_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Artifact written: %s", path)
    return path
