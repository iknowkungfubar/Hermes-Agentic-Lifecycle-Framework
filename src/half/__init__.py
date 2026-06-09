"""HALF — Hermes Agentic Lifecycle Framework.

A modular, template-driven framework that transforms high-level business
concepts into production-ready software through autonomous, multi-agent
orchestration.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Hermes Agent / Turin Tech Solutions"
__license__ = "MIT"
__description__ = "Hermes Agentic Lifecycle Framework — transform concepts into production software"

import sys as _sys

# Check Python version
if _sys.version_info < (3, 13):
    msg = (
        f"HALF requires Python 3.13+. "
        f"You are running Python {_sys.version_info.major}.{_sys.version_info.minor}."
    )
    raise RuntimeError(msg)
