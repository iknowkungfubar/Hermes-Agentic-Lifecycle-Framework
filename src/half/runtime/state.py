"""
HALF — LangGraph State Graph Definitions

TypedDict state definitions for the SDLC state machine.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class PhaseArtifact(TypedDict):
    """A single phase artifact."""

    name: str
    path: str
    content: str
    checksum: str
    phase: str


class GateResult(TypedDict):
    """Result of a gate check."""

    gate_id: str
    passed: bool
    details: str
    timestamp: str


class HalfState(TypedDict):
    """Overall state of the HALF SDLC execution graph."""

    # Project metadata
    project_name: str
    mode: str  # full, prototype, patch, audit

    # Current execution position
    current_phase: str
    current_step: str
    iteration_count: int

    # Phase artifacts (accumulates across phases)
    artifacts: list[PhaseArtifact]

    # Gate results
    gate_results: list[GateResult]

    # Fail-safe state
    retry_count: int
    max_retries: int
    escalation_level: int  # 0=none, 1=step, 2=phase, 3=human, 4=abort

    # Error budget
    error_budget_remaining: int

    # Messages (for LangGraph message passing)
    messages: Annotated[list[dict[str, Any]], add_messages]

    # Agent coordination
    agent_mailbox: dict[str, list[dict[str, Any]]]

    # Production state
    deployment_approved: bool
    mrp_generated: bool


# ─── Phase-Specific State Helpers ─────────────────────────────────────────────


def initial_state(
    project_name: str = "default",
    mode: str = "full",
) -> HalfState:
    """Create the initial HALF state."""
    return HalfState(
        project_name=project_name,
        mode=mode,
        current_phase="phase-1",
        current_step="start",
        iteration_count=0,
        artifacts=[],
        gate_results=[],
        retry_count=0,
        max_retries=3,
        escalation_level=0,
        error_budget_remaining=100,
        messages=[],
        agent_mailbox={},
        deployment_approved=False,
        mrp_generated=False,
    )


def phase_artifacts_dir(state: HalfState, phase: str) -> str:
    """Get the artifacts directory for a given phase."""
    return f".hale/artifacts/{phase}"


def is_gate_passed(state: HalfState, gate_id: str) -> bool:
    """Check if a specific gate has passed."""
    for g in state.get("gate_results", []):
        if g.get("gate_id") == gate_id and g.get("passed"):
            return True
    return False
