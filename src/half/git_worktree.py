"""HALF 1.5 — Git Worktree Isolation for Parallel Swarms.

Each sub-agent gets its own physically isolated working directory and git index
via git worktree add. Enables 5-10 agents to operate in parallel on the same
repository without file-level collisions.

Based on the HALF 1.5 doctrine's 'Git Worktree Isolation' specification.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.git_worktree")


@dataclass
class WorktreeSession:
    """An isolated git worktree for a sub-agent."""

    session_id: str
    agent_name: str
    worktree_path: Path
    branch_name: str
    base_branch: str = "master"
    created_at: str = ""
    active: bool = True
    git_dir: Path | None = None


class GitWorktreeManager:
    """Manages isolated git worktrees for parallel agent execution.

    Each sub-agent gets its own directory with a detached git index,
    preventing file collisions during parallel code generation.

    Usage:
        manager = GitWorktreeManager(repo_path=".")
        session = manager.create_worktree("coder-1", "feat/add-auth")
        # coder-1 works in .worktrees/coder-1/
        # Other agents work in their own worktrees simultaneously
        manager.merge_back(session.session_id)
    """

    def __init__(
        self, repo_path: str | Path = ".", worktree_base: str | Path = ".worktrees"
    ):
        try:
            self.repo_path = Path(repo_path).resolve()
        except (FileNotFoundError, OSError):
            self.repo_path = Path("/tmp/half-worktrees") / Path(repo_path).name
        try:
            self.worktree_base = Path(worktree_base).resolve()
        except (FileNotFoundError, OSError):
            self.worktree_base = Path("/tmp/half-worktrees") / Path(worktree_base).name
        self.worktree_base.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, WorktreeSession] = {}

    def create_worktree(
        self,
        agent_name: str,
        branch_name: str = "",
        base_branch: str = "master",
    ) -> WorktreeSession:
        """Create an isolated worktree for an agent.

        Args:
            agent_name: Agent identifier (used as dir name and branch name).
            branch_name: Git branch for the worktree. Auto-generated if empty.
            base_branch: Branch to fork from.

        Returns:
            WorktreeSession with isolated path.

        Raises:
            RuntimeError: If git worktree creation fails.
        """
        from datetime import datetime

        session_id = f"{agent_name}-{datetime.now(tz=UTC).strftime('%H%M%S')}"
        if not branch_name:
            branch_name = f"agent/{agent_name}"

        worktree_path = self.worktree_base / agent_name

        try:
            # Create the branch if it doesn't exist
            subprocess.run(
                ["git", "branch", branch_name, base_branch],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.repo_path),
            )

            # Create the worktree
            result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch_name],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.repo_path),
            )
            if result.returncode != 0:
                msg = f"git worktree add failed: {result.stderr}"
                raise RuntimeError(msg)

            session = WorktreeSession(
                session_id=session_id,
                agent_name=agent_name,
                worktree_path=worktree_path,
                branch_name=branch_name,
                base_branch=base_branch,
                created_at=datetime.now(tz=UTC).isoformat(),
                git_dir=worktree_path / ".git",
            )
            self._sessions[session_id] = session
            logger.info(
                "Worktree: Created '%s' at %s (branch: %s)",
                agent_name,
                worktree_path,
                branch_name,
            )
            return session

        except subprocess.TimeoutExpired:
            msg = f"git worktree creation timed out for {agent_name}"
            raise RuntimeError(msg)
        except FileNotFoundError:
            msg = "git not found in PATH"
            raise RuntimeError(msg)

    def get_session(self, session_id: str) -> WorktreeSession | None:
        """Get a worktree session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            WorktreeSession if found.
        """
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[WorktreeSession]:
        """List all active worktree sessions.

        Returns:
            List of active sessions.
        """
        return [s for s in self._sessions.values() if s.active]

    def merge_back(
        self, session_id: str, delete_worktree: bool = True
    ) -> dict[str, Any]:
        """Merge a worktree's changes back to the main repo.

        Args:
            session_id: Session to merge.
            delete_worktree: Whether to remove the worktree after merge.

        Returns:
            Dict with merge status, conflicts, and summary.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"status": "error", "message": f"Session {session_id} not found"}

        try:
            # Verify the worktree path exists
            if not session.worktree_path.exists():
                return {
                    "status": "error",
                    "message": f"Worktree path {session.worktree_path} not found",
                }

            # Commit any pending changes in the worktree
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(session.worktree_path),
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "-m",
                    f"feat: work from agent '{session.agent_name}'",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(session.worktree_path),
            )

            # Fetch the worktree branch into main repo
            subprocess.run(
                ["git", "fetch", self.repo_path.stem or ".", session.branch_name],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.repo_path),
            )

            # Merge into base branch
            merge_result = subprocess.run(
                ["git", "merge", session.branch_name, "--no-edit"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.repo_path),
            )

            has_conflicts = (
                "CONFLICT" in merge_result.stdout or "CONFLICT" in merge_result.stderr
            )

            # Clean up worktree
            if delete_worktree:
                subprocess.run(
                    [
                        "git",
                        "worktree",
                        "remove",
                        str(session.worktree_path),
                        "--force",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(self.repo_path),
                )
                subprocess.run(
                    ["git", "branch", "-D", session.branch_name],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(self.repo_path),
                )

            session.active = False
            logger.info(
                "Worktree: Merged '%s' (conflicts: %s)",
                session.agent_name,
                has_conflicts,
            )

            return {
                "status": "merged" if not has_conflicts else "conflicts",
                "session_id": session_id,
                "agent": session.agent_name,
                "branch": session.branch_name,
                "has_conflicts": has_conflicts,
                "merge_output": merge_result.stdout[:500],
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Merge timed out"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def remove_worktree(self, session_id: str) -> bool:
        """Force-remove a worktree without merging.

        Args:
            session_id: Session to remove.

        Returns:
            True if removed successfully.
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(session.worktree_path), "--force"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.repo_path),
            )
            subprocess.run(
                ["git", "branch", "-D", session.branch_name],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.repo_path),
            )
            session.active = False
            logger.info("Worktree: Removed '%s'", session.agent_name)
            return True
        except Exception as e:
            logger.warning("Worktree: Failed to remove '%s': %s", session.agent_name, e)
            return False
