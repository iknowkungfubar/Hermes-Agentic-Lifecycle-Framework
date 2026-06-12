"""HALF 1.5 — RLVMR: Reinforcement Learning with Verifiable Meta-Reasoning.

Tags cognitive steps (planning, exploration, reflection) and receives
programmatic rewards for verifiable, efficient problem-solving.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("half.rlvmr")


class CognitiveStep:
    PLANNING = "planning"
    EXPLORATION = "exploration"
    REFLECTION = "reflection"
    EXECUTION = "execution"
    VERIFICATION = "verification"


@dataclass
class CognitiveTag:
    step_type: str
    description: str
    timestamp: str = ""
    token_cost: int = 0
    reward: float = 0.0
    success: bool = False


@dataclass
class RLVMRRun:
    run_id: str
    task: str
    steps: list[CognitiveTag] = field(default_factory=list)
    total_reward: float = 0.0
    total_tokens: int = 0
    efficiency_score: float = 0.0


class RLVMRTracker:
    REWARDS = {
        CognitiveStep.PLANNING: {"success": 0.5, "failure": 0.0},
        CognitiveStep.EXPLORATION: {"success": 0.3, "failure": 0.1},
        CognitiveStep.REFLECTION: {"success": 1.0, "failure": 0.2},
        CognitiveStep.EXECUTION: {"success": 0.5, "failure": -0.1},
        CognitiveStep.VERIFICATION: {"success": 0.4, "failure": 0.1},
    }

    def __init__(self) -> None:
        self._runs: dict[str, RLVMRRun] = {}

    def start_run(self, run_id: str, task: str) -> RLVMRRun:
        run = RLVMRRun(run_id=run_id, task=task)
        self._runs[run_id] = run
        return run

    def tag_step(
        self,
        run_id: str,
        step_type: str,
        description: str,
        token_cost: int = 0,
        success: bool = True,
    ) -> CognitiveTag:
        run = self._runs.get(run_id)
        if not run:
            run = self.start_run(run_id, description)
        rewards = self.REWARDS.get(step_type, {"success": 0.2, "failure": 0.0})
        reward = rewards["success"] if success else rewards["failure"]
        tag = CognitiveTag(
            step_type=step_type,
            description=description,
            timestamp=datetime.now(tz=UTC).isoformat(),
            token_cost=token_cost,
            reward=reward,
            success=success,
        )
        run.steps.append(tag)
        run.total_reward += reward
        run.total_tokens += token_cost
        return tag

    def calculate_efficiency(self, run_id: str) -> float:
        import math

        run = self._runs.get(run_id)
        if not run or run.total_tokens == 0:
            return 0.0
        run.efficiency_score = run.total_reward / max(1, math.sqrt(run.total_tokens))
        return run.efficiency_score

    def get_summary(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get(run_id)
        if not run:
            return {"error": f"Run {run_id} not found"}
        step_counts: dict[str, dict[str, int]] = {}
        for step in run.steps:
            if step.step_type not in step_counts:
                step_counts[step.step_type] = {"total": 0, "success": 0}
            step_counts[step.step_type]["total"] += 1
            if step.success:
                step_counts[step.step_type]["success"] += 1
        return {
            "run_id": run_id,
            "task": run.task[:100],
            "total_steps": len(run.steps),
            "total_reward": round(run.total_reward, 3),
            "total_tokens": run.total_tokens,
            "efficiency_score": round(self.calculate_efficiency(run_id), 3),
            "step_breakdown": step_counts,
        }

    def get_best_strategy(self) -> str:
        if not self._runs:
            return "No runs recorded yet"
        best_run = max(self._runs.values(), key=lambda r: r.total_reward)
        ps = sum(1 for s in best_run.steps if s.step_type == CognitiveStep.PLANNING)
        es = sum(1 for s in best_run.steps if s.step_type == CognitiveStep.EXPLORATION)
        rs = sum(1 for s in best_run.steps if s.step_type == CognitiveStep.REFLECTION)
        return (
            f"Best run '{best_run.run_id}': {best_run.total_reward:.1f} reward, "
            f"{ps} plan, {es} explore, {rs} reflect steps"
        )
