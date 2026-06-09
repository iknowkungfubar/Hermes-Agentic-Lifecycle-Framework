"""
HALF — LangGraph State Graph Definition

Full SDLC state machine graph:
- 5 phase sub-graphs with tri-phasic execution loops
- Gate check nodes between phases
- Interrupt before human checkpoints (Phase 1, 3, 4 gates)
- Fail-safe escalation routes
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from src.runtime.checkpointer import create_secure_checkpointer
from src.runtime.nodes import (
    phase_1_architecture,
    phase_1_discovery,
    phase_1_gate,
    phase_1_specification,
    phase_2_gate,
    phase_2_implement,
    phase_2_plan,
    phase_2_research,
    phase_2_scaffold,
    phase_2_simplify,
    phase_3_gate,
    phase_3_integration,
    phase_3_security,
    phase_3_testing,
    phase_4_cicd,
    phase_4_gate,
    phase_4_infrastructure,
    phase_4_launch,
    phase_5_codify,
    phase_5_gate,
    phase_5_iterate,
    phase_5_observe,
    route_from_finality_gate,
    route_from_gate,
)
from src.runtime.state import HalfState, initial_state

logger = logging.getLogger("half.runtime.graph")


# ─── Graph Builder ────────────────────────────────────────────────────────────


def build_half_graph() -> StateGraph:  # type: ignore[type-arg]
    """Build the complete HALF SDLC state machine graph.

    Graph structure:
        PHASE 1: discovery → specification → architecture → GATE1 →
        PHASE 2: scaffold → implement → GATE2 →
        PHASE 3: testing → security → integration → GATE3 →
        PHASE 4: infrastructure → cicd → launch → FINALITY GATE →
        PHASE 5: observe → iterate → codify → GATE5 →
        END (cycle back to PHASE 1 for next iteration)

    Human interrupts occur at:
        - After Phase 1 Gate (review spec + architecture)
        - After Phase 3 Gate (review test + security report)
        - After Phase 4 Finality Gate (sign MRP for deployment)

    Returns:
        Compiled StateGraph ready for execution.
    """
    workflow = StateGraph(HalfState)

    # ─── Phase 1 Nodes ────────────────────────────────────────────────────
    workflow.add_node("phase_1_discovery", phase_1_discovery)
    workflow.add_node("phase_1_specification", phase_1_specification)
    workflow.add_node("phase_1_architecture", phase_1_architecture)
    workflow.add_node("phase_1_gate", phase_1_gate)

    # ─── Phase 2 Nodes (Tri-Phasic Loop) ──────────────────────────────────
    workflow.add_node("phase_2_scaffold", phase_2_scaffold)
    workflow.add_node("phase_2_research", phase_2_research)
    workflow.add_node("phase_2_plan", phase_2_plan)
    workflow.add_node("phase_2_implement", phase_2_implement)
    workflow.add_node("phase_2_simplify", phase_2_simplify)
    workflow.add_node("phase_2_gate", phase_2_gate)

    # ─── Phase 3 Nodes ────────────────────────────────────────────────────
    workflow.add_node("phase_3_testing", phase_3_testing)
    workflow.add_node("phase_3_security", phase_3_security)
    workflow.add_node("phase_3_integration", phase_3_integration)
    workflow.add_node("phase_3_gate", phase_3_gate)

    # ─── Phase 4 Nodes ────────────────────────────────────────────────────
    workflow.add_node("phase_4_infrastructure", phase_4_infrastructure)
    workflow.add_node("phase_4_cicd", phase_4_cicd)
    workflow.add_node("phase_4_launch", phase_4_launch)
    workflow.add_node("phase_4_finality_gate", phase_4_gate)

    # ─── Phase 5 Nodes ────────────────────────────────────────────────────
    workflow.add_node("phase_5_observe", phase_5_observe)
    workflow.add_node("phase_5_iterate", phase_5_iterate)
    workflow.add_node("phase_5_codify", phase_5_codify)
    workflow.add_node("phase_5_gate", phase_5_gate)

    # ─── Fail-Safe & Routing Nodes ────────────────────────────────────────
    workflow.add_node("retry_phase", _retry_node)
    workflow.add_node("fail_safe_escalate", _fail_safe_node)
    workflow.add_node("wait_for_signoff", _wait_node)
    workflow.add_node("pipeline_complete", _complete_node)
    workflow.add_node("deploy", _deploy_node)

    # ─── Phase 1 Edges ────────────────────────────────────────────────────
    workflow.add_edge("phase_1_discovery", "phase_1_specification")
    workflow.add_edge("phase_1_specification", "phase_1_architecture")
    workflow.add_edge("phase_1_architecture", "phase_1_gate")
    workflow.add_conditional_edges(
        "phase_1_gate",
        route_from_gate,
        {
            "advance_to_phase-2": "phase_2_scaffold",
            "retry_phase": "retry_phase",
            "fail_safe_escalate": "fail_safe_escalate",
        },
    )

    # ─── Phase 2 Edges (Tri-Phasic Loop) ──────────────────────────────────
    # Scaffold → Research (read-only) → Plan (design-only)
    # → Implement (write-restricted) → Simplify (refactoring) → Gate
    workflow.add_edge("phase_2_scaffold", "phase_2_research")
    workflow.add_edge("phase_2_research", "phase_2_plan")
    workflow.add_edge("phase_2_plan", "phase_2_implement")
    workflow.add_edge("phase_2_implement", "phase_2_simplify")
    workflow.add_edge("phase_2_simplify", "phase_2_gate")
    workflow.add_conditional_edges(
        "phase_2_gate",
        route_from_gate,
        {
            "advance_to_phase-3": "phase_3_testing",
            "retry_phase": "retry_phase",
            "fail_safe_escalate": "fail_safe_escalate",
        },
    )

    # ─── Phase 3 Edges ────────────────────────────────────────────────────
    workflow.add_edge("phase_3_testing", "phase_3_security")
    workflow.add_edge("phase_3_security", "phase_3_integration")
    workflow.add_edge("phase_3_integration", "phase_3_gate")
    workflow.add_conditional_edges(
        "phase_3_gate",
        route_from_gate,
        {
            "advance_to_phase-4": "phase_4_infrastructure",
            "retry_phase": "retry_phase",
            "fail_safe_escalate": "fail_safe_escalate",
        },
    )

    # ─── Phase 4 Edges ────────────────────────────────────────────────────
    workflow.add_edge("phase_4_infrastructure", "phase_4_cicd")
    workflow.add_edge("phase_4_cicd", "phase_4_launch")
    workflow.add_edge("phase_4_launch", "phase_4_finality_gate")
    workflow.add_conditional_edges(
        "phase_4_finality_gate",
        route_from_finality_gate,
        {
            "deploy": "deploy",
            "wait_for_signoff": "wait_for_signoff",
        },
    )

    # ─── Phase 5 Edges ────────────────────────────────────────────────────
    workflow.add_edge("deploy", "phase_5_observe")
    workflow.add_edge("phase_5_observe", "phase_5_iterate")
    workflow.add_edge("phase_5_iterate", "phase_5_codify")
    workflow.add_edge("phase_5_codify", "phase_5_gate")
    workflow.add_conditional_edges(
        "phase_5_gate",
        route_from_gate,
        {
            "advance_to_phase-1": "phase_1_discovery",  # Cycle back
            "retry_phase": "retry_phase",
            "fail_safe_escalate": "fail_safe_escalate",
            "pipeline_complete": "pipeline_complete",
        },
    )

    # ─── Routing edges ────────────────────────────────────────────────────
    workflow.add_edge("retry_phase", "phase_1_discovery")
    workflow.add_edge("fail_safe_escalate", END)
    workflow.add_edge("wait_for_signoff", END)
    workflow.add_edge("pipeline_complete", END)

    return workflow


# ─── Routing Node Implementations ─────────────────────────────────────────────


def _retry_node(state: HalfState) -> dict[str, Any]:
    """Increment retry count and log."""
    retries = state.get("retry_count", 0) + 1
    logger.warning(
        "Retry %d/%d for phase %s",
        retries,
        state.get("max_retries", 3),
        state.get("current_phase"),
    )
    return {
        "retry_count": retries,
        "escalation_level": 1,
        "messages": [
            {"role": "system", "content": f"Retry {retries}: re-running phase"}
        ],
    }


def _fail_safe_node(state: HalfState) -> dict[str, Any]:
    """Escalate to human — generate gap report."""
    logger.critical(
        "Fail-safe escalation for phase %s after %d retries",
        state.get("current_phase"),
        state.get("retry_count", 0),
    )
    return {
        "escalation_level": 3,
        "messages": [
            {
                "role": "system",
                "content": "⚠ FAIL-SAFE ESCALATED — Human intervention required. Gap report generated.",
            }
        ],
    }


def _wait_node(state: HalfState) -> dict[str, Any]:
    """Wait for human sign-off at Finality Gate."""
    logger.info("Finality Gate: waiting for human deployment approval")
    return {
        "current_step": "waiting-for-signoff",
        "messages": [
            {
                "role": "assistant",
                "content": "Finality Gate: MRP ready. Awaiting human deployment approval.",
            }
        ],
    }


def _complete_node(state: HalfState) -> dict[str, Any]:
    """Pipeline complete."""
    logger.info("HALF pipeline complete for %s", state.get("project_name"))
    return {
        "current_step": "complete",
        "messages": [
            {
                "role": "assistant",
                "content": f"HALF pipeline complete for {state.get('project_name')}. Ready for next iteration.",
            }
        ],
    }


def _deploy_node(state: HalfState) -> dict[str, Any]:
    """Execute deployment after Finality Gate approval."""
    logger.info("Deployment approved — executing production deploy")
    return {
        "current_step": "deploying",
        "messages": [
            {
                "role": "assistant",
                "content": "🚀 Deployment executing... MRP signed. Production release in progress.",
            }
        ],
    }


# ─── Compiled Graph Factory ───────────────────────────────────────────────────


def create_half_executor(
    project_name: str = "default",
    mode: str = "full",
    db_path: str = ".hale/state/checkpoints/checkpoints.db",
) -> tuple[Any, HalfState]:
    """Create a fully compiled HALF execution graph with checkpointer.

    Args:
        project_name: Project identifier.
        mode: Pipeline mode (full, prototype, patch, audit).
        db_path: SQLite checkpointer database path.

    Returns:
        Tuple of (compiled_app, initial_state) ready for invocation.
    """
    # Build the graph
    graph = build_half_graph()

    # Create secure checkpointer with WAL
    checkpointer = create_secure_checkpointer(db_path)

    # Compile with interrupt_before for human checkpoints
    app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "phase_1_gate",  # Human reviews spec + architecture
            "phase_3_gate",  # Human reviews test + security report
            "phase_4_finality_gate",  # Human signs MRP for deployment
        ],
    )

    # Create initial state
    init = initial_state(project_name=project_name, mode=mode)

    return app, init
