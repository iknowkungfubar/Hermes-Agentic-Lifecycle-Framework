"""HALF — Central Configuration.

Single source of truth for all configurable paths and settings.
Replaces 25+ hardcoded `.hale/` paths scattered across the codebase.
"""

from __future__ import annotations

import os
from pathlib import Path

# ─── HALF Home Directory ──────────────────────────────────────────────────────
# All runtime data lives under this directory. Override via env var.
# Default: $PWD/.hale (or $HALF_HOME if set)

_HALF_HOME_ENV = "HALF_HOME"


def get_half_home() -> Path:
    """Get the HALF home directory.

    Respects the HALF_HOME env var. Falls back to .hale/ in cwd.

    Returns:
        Absolute path to the HALF runtime directory.
    """
    env = os.environ.get(_HALF_HOME_ENV)
    if env:
        return Path(env).resolve()
    return Path.cwd() / ".hale"


def get_half_home_relative() -> str:
    """Get the HALF home directory as a relative path string.

    Returns:
        Relative path string (default: ".hale").
    """
    env = os.environ.get(_HALF_HOME_ENV)
    if env:
        return env
    return ".hale"


H = get_half_home_relative()  # Short alias for inline use

# ─── All Configurable Paths ───────────────────────────────────────────────────
# Every path in the system is defined here. No hardcoded .hale/ references
# anywhere else in the codebase.

# Artifacts
ARTIFACTS_DIR = f"{H}/artifacts"
ARTIFACTS_PHASE_1 = f"{ARTIFACTS_DIR}/phase-1"
ARTIFACTS_PHASE_2 = f"{ARTIFACTS_DIR}/phase-2"
ARTIFACTS_PHASE_3 = f"{ARTIFACTS_DIR}/phase-3"
ARTIFACTS_PHASE_4 = f"{ARTIFACTS_DIR}/phase-4"
ARTIFACTS_PHASE_5 = f"{ARTIFACTS_DIR}/phase-5"

# Gates
GATES_DIR = f"{H}/gates"

# Logs
LOGS_DIR = f"{H}/logs"
RETRIES_LOG = f"{LOGS_DIR}/retries.log"

# Metrics
METRICS_DIR = f"{H}/metrics"
ERROR_BUDGET_FILE = f"{METRICS_DIR}/error-budget.json"

# State / Checkpoints
STATE_DIR = f"{H}/state"
CHECKPOINTS_DIR = f"{STATE_DIR}/checkpoints"
CHECKPOINTS_DB = f"{CHECKPOINTS_DIR}/checkpoints.db"

# Agent Mail
AGENT_MAIL_DIR = f"{H}/agent-mail"
AGENT_MAIL_DB = f"{AGENT_MAIL_DIR}/mail.db"

# Security
SECURITY_DIR = f"{H}/security"
FINALITY_GATE_FILE = f"{H}/finality-gate.json"

# Config
CONFIG_FILE = f"{H}/config.yaml"
FAIL_SAFES_CONFIG = f"{H}/fail-safes.yaml"
LOOPSCRIPT_FILE = f"{H}/loopscript.yaml"
INDEXING_CONFIG = f"{H}/indexing.yaml"
SAFETY_CONFIG = f"{H}/safety.yaml"

# Voice
VOICE_MODELS_DIR = f"{H}/voice-models"

# Templates
TEMPLATES_DIR = f"{H}/templates"
FOSS_DIR = f"{H}/foss"

# Scripts
SCRIPTS_DIR = f"{H}/scripts"

# Security scan
BANDIT_REPORT = f"{SECURITY_DIR}/bandit.json"
SEMGREP_REPORT = f"{SECURITY_DIR}/semgrep.json"

# MRP
MRP_FILE = f"{ARTIFACTS_DIR}/phase-4/mrp.json"
ROLLBACK_PLAN_FILE = f"{ARTIFACTS_DIR}/phase-4/rollback-plan.md"

# ─── Directory Creation Helper ────────────────────────────────────────────────


def ensure_dirs() -> None:
    """Create all required HALF directories."""
    dirs = [
        ARTIFACTS_DIR,
        ARTIFACTS_PHASE_1,
        ARTIFACTS_PHASE_2,
        ARTIFACTS_PHASE_3,
        ARTIFACTS_PHASE_4,
        ARTIFACTS_PHASE_5,
        GATES_DIR,
        LOGS_DIR,
        METRICS_DIR,
        STATE_DIR,
        CHECKPOINTS_DIR,
        AGENT_MAIL_DIR,
        SECURITY_DIR,
        VOICE_MODELS_DIR,
        TEMPLATES_DIR,
        FOSS_DIR,
        SCRIPTS_DIR,
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
