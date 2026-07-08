"""Routing logic for HALF LangGraph nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from half.runtime.state import HalfState


def route_from_gate(state: HalfState) -> str:
    """Route to next phase or fail-safe based on gate result."""
    gate_results = state.get("gate_results", [])
    if not gate_results:
        return "fail_safe_escalate"

    last_gate = gate_results[-1]
    if last_gate.get("passed", False):
        current = state.get("current_phase", "phase-1")
        phase_order = ["phase-1", "phase-2", "phase-3", "phase-4", "phase-5"]
        try:
            idx = phase_order.index(current)
            if idx < len(phase_order) - 1:
                return f"advance_to_{phase_order[idx + 1]}"
            return "pipeline_complete"
        except ValueError:
            return "fail_safe_escalate"
    else:
        retries = state.get("retry_count", 0)
        if retries < state.get("max_retries", 3):
            return "retry_phase"
        return "fail_safe_escalate"


def route_from_finality_gate(state: HalfState) -> str:
    """Route after Finality Gate: deploy or wait."""
    if state.get("deployment_approved", False):
        return "deploy"
    return "wait_for_signoff"
