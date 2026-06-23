"""HALF — Hermes Agentic Lifecycle Framework.

A modular, template-driven framework that transforms high-level business
concepts into production-ready software through autonomous, multi-agent
orchestration.
"""

from __future__ import annotations

import sys as _sys

# Read version from package metadata (single source of truth in pyproject.toml)
try:
    from importlib.metadata import version as _metadata_version

    __version__ = _metadata_version("hermes-half")
except Exception:
    __version__ = "1.0.0"

__author__ = "Hermes Agent / Turin Tech Solutions"
__license__ = "MIT"
__description__ = (
    "Hermes Agentic Lifecycle Framework — transform concepts into production software"
)

# Check Python version
