"""HALF 1.5 — BranchFS: Speculative Branch Execution.

Spawns parallel speculative agent branches to explore multiple approaches
simultaneously. Each branch operates in isolated git worktrees. Results are
compared and the best approach is merged.

Based on the HALF 1.5 doctrine's 'BranchFS' and 'speculative branches' spec.
"""

from __future__ import annotations

import logging
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from half.git_worktree import GitWorktreeManager

logger = logging.getLogger("half.branchfs")


@dataclass
class SpeculativeBranch:
    """A single speculative execution branch."""

    branch_id: str
    approach_name: str
    description: str
    worktree_path: Path
    branch_name: str
    status: str = "running"  # running, completed, failed, pruned
    result_summary: str = ""
    score: float = 0.0  # Evaluation score for comparison
    created_at: str = ""
    completed_at: str = ""


class BranchFS:
    """Speculative Branch File System.

    Spawns multiple parallel agent branches, each exploring a different
    approach to the same problem. After all branches complete, compares
    results and selects the best approach for merging.

    Usage:
        bfs = BranchFS()
        branches = bfs.spawn("Add auth middleware", [
            ("jwt", "Use JWT tokens stored in HTTP-only cookies"),
            ("session", "Use server-side sessions with Redis"),
            ("api-key", "Use API keys in headers"),
        ])
        # Each branch runs in its own git worktree
        bfs.compare_and_select(branches)
    """

    def __init__(self, repo_path: str | Path = "."):
        self.repo_path = Path(repo_path)
        self.git_worktree = GitWorktreeManager(repo_path)
        self._branches: dict[str, SpeculativeBranch] = {}

    def spawn(
        self,
        task_name: str,
        approaches: list[tuple[str, str]],
    ) -> list[SpeculativeBranch]:
        """Spawn multiple speculative branches, each exploring an approach.

        Args:
            task_name: Name of the task.
            approaches: List of (approach_name, description) tuples.

        Returns:
            List of SpeculativeBranch instances.
        """
        branches: list[SpeculativeBranch] = []
        now = datetime.now(tz=timezone.utc)

        for approach_name, description in approaches:
            branch_id = f"branch-{uuid.uuid4().hex[:6]}"
            safe_name = approach_name.lower().replace(" ", "-").replace("/", "-")

            try:
                session = self.git_worktree.create_worktree(
                    agent_name=safe_name,
                    branch_name=f"spec/{safe_name}",
                    base_branch="master",
                )

                branch = SpeculativeBranch(
                    branch_id=branch_id,
                    approach_name=approach_name,
                    description=description,
                    worktree_path=session.worktree_path,
                    branch_name=session.branch_name,
                    status="running",
                    created_at=now.isoformat(),
                )
                self._branches[branch_id] = branch
                branches.append(branch)
                logger.info("BranchFS: Spawned '%s' at %s", approach_name, session.worktree_path)

            except RuntimeError as e:
                logger.error("BranchFS: Failed to spawn '%s': %s", approach_name, e)

        return branches

    def mark_completed(self, branch_id: str, score: float, summary: str = "") -> None:
        """Mark a speculative branch as completed.

        Args:
            branch_id: Branch identifier.
            score: Evaluation score (0.0-1.0).
            summary: Result summary.
        """
        branch = self._branches.get(branch_id)
        if branch:
            branch.status = "completed"
            branch.score = score
            branch.result_summary = summary
            branch.completed_at = datetime.now(tz=timezone.utc).isoformat()
            logger.info("BranchFS: '%s' completed (score=%.2f)", branch.approach_name, score)

    def compare_and_select(self, branches: list[SpeculativeBranch]) -> SpeculativeBranch:
        """Compare completed branches and select the best approach.

        Args:
            branches: List of branches to compare.

        Returns:
            The winning branch.
        """
        completed = [b for b in branches if b.status == "completed"]
        if not completed:
            raise ValueError("No completed branches to compare")

        # Sort by score descending
        completed.sort(key=lambda b: b.score, reverse=True)
        winner = completed[0]

        logger.info(
            "BranchFS: Selected '%s' (score=%.2f) from %d branches",
            winner.approach_name, winner.score, len(completed),
        )
        return winner

    def prune_losers(self, winner: SpeculativeBranch) -> None:
        """Remove losing branches.

        Args:
            winner: The winning branch (not pruned).
        """
        for bid, branch in self._branches.items():
            if branch.branch_id != winner.branch_id and branch.status == "completed":
                self.git_worktree.remove_worktree(bid)
                branch.status = "pruned"
                logger.info("BranchFS: Pruned '%s'", branch.approach_name)

    def get_all_branches(self) -> list[SpeculativeBranch]:
        """Get all speculative branches.

        Returns:
            List of all branches.
        """
        return list(self._branches.values())

    def get_active_branches(self) -> list[SpeculativeBranch]:
        """Get currently running branches.

        Returns:
            List of running branches.
        """
        return [b for b in self._branches.values() if b.status == "running"]
