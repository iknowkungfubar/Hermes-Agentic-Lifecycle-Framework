"""HALF — Data models for task routing decisions and LoopScript DAGs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from half.routing.enums import TaskDomain, WorkflowType


@dataclass
class RoutingDecision:
    """Result of routing a task to a workflow."""

    task_description: str
    domain: TaskDomain
    workflow: WorkflowType
    confidence: float  # 0.0 to 1.0
    requires_psm: bool = False  # Portable Skill Module needed
    psm_hints: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class LoopScriptTask:
    """A single task in a LoopScript DAG."""

    id: str
    name: str
    agent: str
    mode: str  # read-only, design-only, write-restricted
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class LoopScript:
    """A declarative DAG configuration for task execution."""

    version: str = "1.0"
    phases: list[LoopScriptTask] = field(default_factory=list)
    chain: list[str] = field(default_factory=list)
    tri_phasic: list[str] = field(default_factory=list)
