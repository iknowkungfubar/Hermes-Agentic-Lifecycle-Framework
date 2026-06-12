"""HALF — Meta-Reasoning: Adaptive Execution Logic.

Tree-of-Thoughts (ToT) and ReAct style execution auditing.
The Commander Agent continuously monitors sub-agent workflow progression,
detects stalled success metrics, and dynamically alters reasoning paths.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("half.meta_reasoning")


@dataclass
class ReasoningTrace:
    """A single step in the reasoning tree."""

    step_id: str
    parent_id: str | None = None
    action: str = ""
    observation: str = ""
    success_metric: float = 0.0
    confidence: float = 1.0
    terminated: bool = False
    branches: list[str] = field(default_factory=list)


class MetaReasoningEngine:
    """Adaptive execution logic with Tree-of-Thoughts reasoning.

    Continuously audits sub-agent workflow progression. If a sub-agent
    begins hallucinating, detects the stalled success metric and
    dynamically alters the reasoning path.
    """

    def __init__(self, stagnation_threshold: float = 0.1, max_iterations: int = 3):
        self.stagnation_threshold = stagnation_threshold
        self.max_iterations = max_iterations
        self._traces: dict[str, ReasoningTrace] = {}
        self._iteration = 0

    def start_trace(self, action: str) -> ReasoningTrace:
        trace = ReasoningTrace(step_id="root", action=action)
        self._traces["root"] = trace
        self._iteration = 0
        logger.info("Meta-Reasoning: Started trace for '%s'", action)
        return trace

    def add_step(
        self,
        parent_id: str,
        action: str,
        observation: str,
        success_metric: float,
    ) -> ReasoningTrace:
        step_id = f"step-{len(self._traces)}"
        parent = self._traces.get(parent_id)
        if parent:
            parent.branches.append(step_id)
        trace = ReasoningTrace(
            step_id=step_id,
            parent_id=parent_id,
            action=action,
            observation=observation,
            success_metric=success_metric,
        )
        self._traces[step_id] = trace
        self._iteration += 1
        return trace

    def should_terminate_branch(self, step_id: str) -> bool:
        if self._iteration >= self.max_iterations:
            return True
        trace = self._traces.get(step_id)
        if not trace:
            return False
        if self._iteration > 1:
            parent = self._traces.get(trace.parent_id) if trace.parent_id else None
            if (
                parent
                and trace.success_metric
                <= parent.success_metric + self.stagnation_threshold
            ):
                if self._iteration >= 2:
                    return True
        return False

    def prune_branch(self, step_id: str) -> ReasoningTrace | None:
        trace = self._traces.get(step_id)
        if not trace:
            return None
        trace.terminated = True
        return self.add_step(
            parent_id=trace.parent_id or "root",
            action=f"ALTERNATIVE: {trace.action}",
            observation="Prior branch terminated — new approach",
            success_metric=0.0,
        )

    def get_best_path(self) -> list[ReasoningTrace]:
        all_ids = set(self._traces.keys())
        child_ids: set[str] = set()
        for trace_val in self._traces.values():
            child_ids.update(trace_val.branches)
        leaf_ids = all_ids - child_ids
        if not leaf_ids:
            root = self._traces.get("root")
            return [root] if root else []
        best_id = max(leaf_ids, key=lambda i: self._traces[i].success_metric)
        path: list[ReasoningTrace] = []
        current: str | None = best_id
        while current:
            t: ReasoningTrace | None = self._traces.get(current)
            if t:
                path.insert(0, t)
                current = t.parent_id
            else:
                break
        return path

    def generate_report(self) -> str:
        best_path = self.get_best_path()
        lines = [
            "# Meta-Reasoning Report",
            f"**Total steps:** {len(self._traces)}",
            f"**Iterations:** {self._iteration}",
            "",
            "## Reasoning Tree",
        ]
        for trace in self._traces.values():
            indent = "  " if trace.parent_id else ""
            status = "✓" if not trace.terminated else "✗"
            lines.append(
                f"{indent}- [{status}] {trace.action[:60]} "
                f"(metric={trace.success_metric:.2f})"
            )
        lines.extend(["", "## Best Path"])
        for step in best_path:
            lines.append(f"- {step.action} -> {step.observation[:60]}")
        return "\n".join(lines)
