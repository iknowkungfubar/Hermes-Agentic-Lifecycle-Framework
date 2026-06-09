"""
HALF — LangGraph Runtime

Complete SDLC state machine with:
- 5-phase state graph with tri-phasic execution loops
- SQLite checkpointer with WAL mode
- Metadata allowlist security (CVE-2025-67644, CVE-2026-28277)
- Interrupt_before for human checkpoints
- Fail-safe escalation routes
"""

from __future__ import annotations

from half.runtime.checkpointer import create_secure_checkpointer, get_checkpoint_paths
from half.runtime.graph import build_half_graph, create_half_executor
from half.runtime.nodes import (
    route_from_finality_gate,
    route_from_gate,
)
from half.runtime.state import HalfState, initial_state, is_gate_passed

__all__ = [
    "HalfState",
    "build_half_graph",
    "create_half_executor",
    "create_secure_checkpointer",
    "get_checkpoint_paths",
    "initial_state",
    "is_gate_passed",
    "route_from_finality_gate",
    "route_from_gate",
]
