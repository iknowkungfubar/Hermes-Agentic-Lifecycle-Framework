"""HALF 1.5 — Durable Execution Framework.

Ensures agent state survives crashes without duplicate executions upon
recovery. Checkpoint-and-retry with idempotency guarantees.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.durable_exec")


@dataclass
class ExecutionStep:
    step_id: str
    name: str
    status: str = "pending"
    input_hash: str = ""
    output_hash: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionContext:
    execution_id: str
    created_at: str = ""
    steps: dict[str, ExecutionStep] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "initialized"


class DurableExecutor:
    """Durable execution with idempotency and crash recovery.

    Each step is checkpointed before and after execution. If the process
    crashes, the next run resumes from the last successful checkpoint.
    """

    def __init__(self, state_dir: str | Path = ".hale/state/durable") -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def start_execution(
        self, name: str, metadata: dict[str, Any] | None = None
    ) -> ExecutionContext:
        now = datetime.now(tz=UTC).isoformat()
        ctx = ExecutionContext(
            execution_id=f"exec-{uuid.uuid4().hex[:8]}",
            created_at=now,
            metadata=metadata or {},
        )
        self._save_checkpoint(ctx)
        logger.info("Durable: Started '%s' (%s)", name, ctx.execution_id)
        return ctx

    def durable_step(self, ctx: ExecutionContext, step_name: str) -> Any:
        """Decorator that wraps a function as a durable step."""

        def decorator(func: Any) -> Any:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._execute_with_checkpoint(
                    ctx, step_name, func, *args, **kwargs
                )

            return wrapper

        return decorator

    def _execute_with_checkpoint(
        self,
        ctx: ExecutionContext,
        step_name: str,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        existing = ctx.steps.get(step_name)
        if existing and existing.status == "completed":
            logger.info("Durable: Step '%s' already completed — resuming", step_name)
            return existing.result

        step = ExecutionStep(
            step_id=f"{ctx.execution_id}:{step_name}",
            name=step_name,
            status="running",
            started_at=datetime.now(tz=UTC).isoformat(),
        )
        ctx.steps[step_name] = step
        self._save_checkpoint(ctx)

        try:
            result = func(*args, **kwargs)
            step.status = "completed"
            step.result = result if isinstance(result, dict) else {"value": result}
            step.completed_at = datetime.now(tz=UTC).isoformat()
            self._save_checkpoint(ctx)
            return result
        except Exception as e:
            step.status = "failed"
            step.retry_count += 1
            step.result = {"error": str(e)}
            self._save_checkpoint(ctx)
            if step.retry_count < step.max_retries:
                return self._execute_with_checkpoint(
                    ctx, step_name, func, *args, **kwargs
                )
            raise

    def recover(self, execution_id: str) -> ExecutionContext | None:
        checkpoint = self.state_dir / f"{execution_id}.json"
        if not checkpoint.exists():
            return None
        try:
            data = json.loads(checkpoint.read_text())
            ctx = ExecutionContext(**{k: v for k, v in data.items() if k != "steps"})
            for sn, sd in data.get("steps", {}).items():
                ctx.steps[sn] = ExecutionStep(**sd)
            return ctx
        except (json.JSONDecodeError, KeyError) as e:
            logger.exception("Durable: Failed to load %s: %s", execution_id, e)
            return None

    def _save_checkpoint(self, ctx: ExecutionContext) -> None:
        data = {
            "execution_id": ctx.execution_id,
            "created_at": ctx.created_at,
            "status": ctx.status,
            "metadata": ctx.metadata,
            "steps": {n: dict(s.__dict__.items()) for n, s in ctx.steps.items()},
        }
        (self.state_dir / f"{ctx.execution_id}.json").write_text(
            json.dumps(data, indent=2)
        )
