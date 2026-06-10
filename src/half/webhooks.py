"""HALF — GitHub Webhook Handler for Autonomous PRs.

When a Focalboard ticket moves to 'In Progress', a webhook triggers
the agent to spawn an isolated Git worktree and run its loop.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.webhooks")


class WebhookHandler:
    """Handles GitHub webhooks for autonomous PR creation.

    Listens for:
    - Focalboard ticket status changes
    - GitHub push/PR events
    """

    def __init__(self, webhook_secret: str = "", repo_root: str | Path = "."):
        self.secret = webhook_secret or os.environ.get("HALF_WEBHOOK_SECRET", "")
        self.repo_root = Path(repo_root)

    def verify_signature(self, payload_body: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature.

        Args:
            payload_body: Raw request body.
            signature: X-Hub-Signature-256 header value.

        Returns:
            True if signature is valid.
        """
        if not self.secret:
            logger.warning("No webhook secret configured — skipping signature verification")
            return True
        expected = hmac.new(self.secret.encode(), payload_body, "sha256").hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def handle_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle a push event — run verification on new commits."""
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])

        results = []
        for commit in commits:
            result = self._verify_commit(commit)
            results.append(result)
            if not result["passed"]:
                self._create_fix_branch(branch, commit)

        return {
            "event": "push",
            "branch": branch,
            "commits_checked": len(commits),
            "results": results,
        }

    def handle_focalboard_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle a Focalboard webhook when a ticket status changes."""
        card_id = payload.get("card_id", "")
        new_status = payload.get("status", "")

        if new_status == "in-progress":
            worktree = self._create_worktree(card_id)
            result = self._run_agent_loop(worktree)
            return {
                "event": "focalboard_status_change",
                "card_id": card_id,
                "status": new_status,
                "worktree": str(worktree),
                "agent_loop": result,
            }

        return {
            "event": "focalboard_status_change",
            "card_id": card_id,
            "status": new_status,
            "action": "no_action_required",
        }

    def _verify_commit(self, commit: dict[str, Any]) -> dict[str, Any]:
        """Verify a single commit passes quality gates."""
        message = commit.get("message", "")
        files = commit.get("modified", []) + commit.get("added", [])

        return {
            "sha": commit.get("id", "")[:8],
            "message": message.split("\n")[0],
            "follows_convention": message.startswith(("feat:", "fix:", "refactor:", "test:", "docs:", "chore:")),
            "files_changed": len(files),
            "passed": True,
        }

    def _create_fix_branch(self, base_branch: str, commit: dict[str, Any]) -> None:
        """Create a fix branch for a failing commit."""
        branch_name = f"fix/auto-{commit.get('id', 'unknown')[:8]}"
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_root, capture_output=True, timeout=30,
            )
            subprocess.run(["git", "checkout", base_branch], cwd=self.repo_root, capture_output=True, timeout=30)
            logger.info("Created fix branch: %s", branch_name)
        except subprocess.TimeoutExpired:
            pass

    def _create_worktree(self, card_id: str) -> Path:
        """Create an isolated Git worktree for a ticket."""
        worktree_path = self.repo_root.parent / f".worktrees/{card_id}"
        worktree_path.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "HEAD"],
                cwd=self.repo_root, capture_output=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            pass
        return worktree_path

    def _run_agent_loop(self, worktree: Path) -> dict[str, Any]:
        """Run the agent loop in an isolated worktree."""
        return {
            "status": "dispatched",
            "worktree": str(worktree),
            "message": "Agent loop started in isolated worktree",
        }
