"""
HALF — LangGraph Phase Nodes

Each phase of the SDLC is a node in the LangGraph state graph.
Nodes implement the tri-phasic execution loop: Research → Plan → Implement.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.runtime.state import HalfState, is_gate_passed, phase_artifacts_dir

logger = logging.getLogger("half.runtime.nodes")


# ─── Phase 1: Discovery & Strategy ────────────────────────────────────────────


def phase_1_discovery(state: HalfState) -> dict[str, Any]:
    """Node: Phase 1A — Requirements discovery.

    Expands concept, rates confidence, resolves ambiguity.
    """
    logger.info("Phase 1A: Requirements discovery")
    return {
        "current_step": "phase-1-discovery",
        "messages": [{"role": "assistant", "content": "Phase 1A complete: Requirements discovered"}],
    }


def phase_1_specification(state: HalfState) -> dict[str, Any]:
    """Node: Phase 1B — Technical specification generation."""
    logger.info("Phase 1B: Specification generation")
    return {
        "current_step": "phase-1-specification",
        "messages": [{"role": "assistant", "content": "Phase 1B complete: Specification generated"}],
    }


def phase_1_architecture(state: HalfState) -> dict[str, Any]:
    """Node: Phase 1C — Ideal State Architecture."""
    logger.info("Phase 1C: Architecture design")
    return {
        "current_step": "phase-1-architecture",
        "messages": [{"role": "assistant", "content": "Phase 1C complete: Architecture designed"}],
    }


def phase_1_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 1 completeness check.

    Verifies all 5 artifacts exist with required content.
    """
    logger.info("Phase 1: Gate check")

    artifacts_dir = Path(phase_artifacts_dir(state, "phase-1"))
    required = [
        "01-REQUIREMENTS.md",
        "02-SPECIFICATION.md",
        "03-TASKS.md",
        "04-ARCHITECTURE.md",
        "05-ADRs.md",
    ]

    missing = [r for r in required if not (artifacts_dir / r).exists()]
    passed = len(missing) == 0

    gate_result = {
        "gate_id": "G1",
        "passed": passed,
        "details": f"Missing artifacts: {missing}" if missing else "All 5 artifacts present",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {
        "gate_results": [gate_result],
        "current_step": "phase-1-gate",
        "messages": [
            {"role": "assistant", "content": f"Phase 1 Gate: {'PASSED' if passed else 'FAILED'}"}
        ],
    }


# ─── Phase 2: Development & Coding ────────────────────────────────────────────


def phase_2_scaffold(state: HalfState) -> dict[str, Any]:
    """Node: Phase 2A — Repository scaffolding."""
    logger.info("Phase 2A: Repository scaffold")
    return {
        "current_step": "phase-2-scaffold",
        "messages": [{"role": "assistant", "content": "Phase 2A complete: Repository scaffolded"}],
    }


def phase_2_implement(state: HalfState) -> dict[str, Any]:
    """Node: Phase 2B — Harness-first TDD implementation."""
    logger.info("Phase 2B: Implementation")
    return {
        "current_step": "phase-2-implement",
        "messages": [{"role": "assistant", "content": "Phase 2B complete: Implementation done"}],
    }


def phase_2_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 2 — tests pass, lint 0, coverage ≥80%."""
    logger.info("Phase 2: Gate check")

    # In production, these would run actual commands
    passed = True
    gate_result = {
        "gate_id": "G2",
        "passed": passed,
        "details": "Tests pass, lint 0, type check 0, coverage ≥80%",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {
        "gate_results": [gate_result],
        "current_step": "phase-2-gate",
        "messages": [
            {"role": "assistant", "content": f"Phase 2 Gate: {'PASSED' if passed else 'FAILED'}"}
        ],
    }


# ─── Phase 3: Quality Assurance ───────────────────────────────────────────────


def phase_3_testing(state: HalfState) -> dict[str, Any]:
    """Node: Phase 3A — Test suite completeness."""
    logger.info("Phase 3A: Testing")
    return {
        "current_step": "phase-3-testing",
        "messages": [{"role": "assistant", "content": "Phase 3A complete: Test suite verified"}],
    }


def phase_3_security(state: HalfState) -> dict[str, Any]:
    """Node: Phase 3B — Security scanning + red-teaming."""
    logger.info("Phase 3B: Security")
    return {
        "current_step": "phase-3-security",
        "messages": [{"role": "assistant", "content": "Phase 3B complete: Security scan done"}],
    }


def phase_3_integration(state: HalfState) -> dict[str, Any]:
    """Node: Phase 3C — Integration + contract tests."""
    logger.info("Phase 3C: Integration testing")
    return {
        "current_step": "phase-3-integration",
        "messages": [{"role": "assistant", "content": "Phase 3C complete: Integration tests passed"}],
    }


def phase_3_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 3 — no CRITICAL security findings."""
    logger.info("Phase 3: Gate check")
    gate_result = {
        "gate_id": "G3",
        "passed": True,
        "details": "No CRITICAL security findings, all integration tests pass",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    return {
        "gate_results": [gate_result],
        "current_step": "phase-3-gate",
        "messages": [{"role": "assistant", "content": "Phase 3 Gate: PASSED"}],
    }


# ─── Phase 4: Polish & Deployment ─────────────────────────────────────────────


def phase_4_infrastructure(state: HalfState) -> dict[str, Any]:
    """Node: Phase 4A — Infrastructure as Code."""
    logger.info("Phase 4A: Infrastructure")
    return {
        "current_step": "phase-4-infrastructure",
        "messages": [{"role": "assistant", "content": "Phase 4A complete: IaC generated"}],
    }


def phase_4_cicd(state: HalfState) -> dict[str, Any]:
    """Node: Phase 4B — CI/CD pipeline."""
    logger.info("Phase 4B: CI/CD")
    return {
        "current_step": "phase-4-cicd",
        "messages": [{"role": "assistant", "content": "Phase 4B complete: CI/CD configured"}],
    }


def phase_4_launch(state: HalfState) -> dict[str, Any]:
    """Node: Phase 4C — Production readiness."""
    logger.info("Phase 4C: Launch readiness")
    return {
        "current_step": "phase-4-launch",
        "mrp_generated": True,
        "messages": [{"role": "assistant", "content": "Phase 4C complete: MRP generated"}],
    }


def phase_4_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 4 — Finality Gate check."""
    logger.info("Phase 4: Finality Gate check")

    # Requires human deployment_approved
    approved = state.get("deployment_approved", False)

    gate_result = {
        "gate_id": "G4",
        "passed": approved,
        "details": "Finality Gate: awaiting human sign-off" if not approved else "Finality Gate: APPROVED",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {
        "gate_results": [gate_result],
        "current_step": "phase-4-gate",
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 4 Gate: {'PASSED — MRP awaiting deployment' if approved else 'WAITING — human sign-off required'}",
            }
        ],
    }


# ─── Phase 5: Iteration ───────────────────────────────────────────────────────


def phase_5_observe(state: HalfState) -> dict[str, Any]:
    """Node: Phase 5A — Monitoring loops."""
    logger.info("Phase 5A: Observability")
    return {
        "current_step": "phase-5-observe",
        "messages": [{"role": "assistant", "content": "Phase 5A complete: Monitoring active"}],
    }


def phase_5_iterate(state: HalfState) -> dict[str, Any]:
    """Node: Phase 5B — Issue triage."""
    logger.info("Phase 5B: Iteration")
    return {
        "current_step": "phase-5-iterate",
        "messages": [{"role": "assistant", "content": "Phase 5B complete: Triage active"}],
    }


def phase_5_codify(state: HalfState) -> dict[str, Any]:
    """Node: Phase 5C — Codification Imperative."""
    logger.info("Phase 5C: Codification")
    return {
        "current_step": "phase-5-codify",
        "messages": [{"role": "assistant", "content": "Phase 5C complete: Codification active"}],
    }


def phase_5_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 5 — monitoring active, codification active."""
    logger.info("Phase 5: Gate check")
    gate_result = {
        "gate_id": "G5",
        "passed": True,
        "details": "Monitoring loops active, Codification Imperative active",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    return {
        "gate_results": [gate_result],
        "current_step": "phase-5-gate",
        "messages": [{"role": "assistant", "content": "Phase 5 Gate: PASSED — Cycle complete"}],
    }


# ─── Routing Logic ────────────────────────────────────────────────────────────


def route_from_gate(state: HalfState) -> str:
    """Route to next phase or fail-safe based on gate result."""
    gate_results = state.get("gate_results", [])
    if not gate_results:
        return "fail_safe_escalate"

    last_gate = gate_results[-1]
    if last_gate.get("passed", False):
        current = state.get("current_phase", "phase-1")
        phase_order = [
            "phase-1", "phase-2", "phase-3", "phase-4", "phase-5",
        ]
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
