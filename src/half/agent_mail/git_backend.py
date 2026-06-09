"""
HALF — Agent Mail: Git Integration Layer

Augments the SQLite-backed Agent Mail with Git version control.
Every message send, lease acquire/release, and agent registration
is recorded as a Git commit in the mail repository, providing
full audit trail and decentralized backup.
"""

from __future__ import annotations
from half import config

import contextlib
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("half.agent_mail.git")


class GitMailBackend:
    """Git integration for Agent Mail.

    Wraps each database write operation with a Git commit, creating
    an auditable, decentralized message history.

    The mail repository lives at .hale/agent-mail/.git/
    alongside the SQLite database.
    """

    def __init__(self, mail_dir: str | Path = config.AGENT_MAIL_DIR):
        self.mail_dir = Path(mail_dir)
        self.mail_dir.mkdir(parents=True, exist_ok=True)
        self._init_repo()

    def _init_repo(self) -> None:
        """Initialize Git repository if it doesn't exist."""
        git_dir = self.mail_dir / ".git"
        if not git_dir.exists():
            self._git("init")
            self._git("config", "user.name", "Agent Mail")
            self._git("config", "user.email", "agent-mail@half.local")

            # Create .gitignore for the mail directory
            ignore_file = self.mail_dir / ".gitignore"
            if not ignore_file.exists():
                ignore_file.write_text("*.db-wal\n*.db-shm\n__pycache__/\n")

            # Initial commit of empty database
            self._git("add", "-A")
            try:
                self._git("commit", "-m", "chore: initialize Agent Mail repository")
            except RuntimeError:
                pass  # No changes to commit

            logger.info("Initialized Git-backed Agent Mail at %s", self.mail_dir)

    def _git(self, *args: str) -> str:
        """Run a Git command in the mail directory.

        Args:
            *args: Git arguments.

        Returns:
            Git command stdout.

        Raises:
            RuntimeError: If Git command fails.
        """
        try:
            result = subprocess.run(
                ["git", *list(args)],
                cwd=str(self.mail_dir),
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "GIT_DIR": str(self.mail_dir / ".git")},
            )
            if result.returncode != 0:
                if "nothing to commit" not in result.stderr:
                    logger.warning("Git warning: %s", result.stderr.strip())
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.exception("Git command timed out: %s", " ".join(args))
            msg = f"Git command timed out: {' '.join(args)}"
            raise RuntimeError(msg)
        except FileNotFoundError:
            logger.warning("Git not found — Agent Mail running without Git backup")
            return ""

    def commit_message_sent(
        self, message_id: str, sender: str, recipients: list[str]
    ) -> None:
        """Record a sent message in Git history.

        Args:
            message_id: Message identifier.
            sender: Sender email.
            recipients: List of recipient emails.
        """
        subject = f"mail: {sender} -> {', '.join(recipients)}"
        body = f"Message {message_id} sent by {sender}"
        self._git("add", "mail.db")
        with contextlib.suppress(RuntimeError):
            self._git("commit", "-m", subject, "-m", body)

    def commit_lease_acquired(self, lease_id: str, file_path: str, agent: str) -> None:
        """Record a file lease acquisition in Git history.

        Args:
            lease_id: Lease identifier.
            file_path: Path of the reserved file.
            agent: Agent email that acquired the lease.
        """
        subject = f"lease: {agent} acquired {file_path}"
        body = f"Lease {lease_id}: {file_path} reserved by {agent}"
        self._git("add", "mail.db")
        with contextlib.suppress(RuntimeError):
            self._git("commit", "-m", subject, "-m", body)

    def commit_lease_released(self, lease_id: str, file_path: str, agent: str) -> None:
        """Record a file lease release in Git history.

        Args:
            lease_id: Lease identifier.
            file_path: Path of the released file.
            agent: Agent email that released the lease.
        """
        subject = f"lease: {agent} released {file_path}"
        body = f"Lease {lease_id}: {file_path} released by {agent}"
        self._git("add", "mail.db")
        with contextlib.suppress(RuntimeError):
            self._git("commit", "-m", subject, "-m", body)

    def commit_agent_registered(self, agent_email: str, role: str) -> None:
        """Record an agent registration in Git history.

        Args:
            agent_email: Registered agent email.
            role: Agent role.
        """
        subject = f"agent: {agent_email} registered as {role}"
        self._git("add", "mail.db")
        with contextlib.suppress(RuntimeError):
            self._git("commit", "-m", subject)

    def get_log(self, max_count: int = 50) -> list[dict[str, str]]:
        """Get the Git commit log for the mail repository.

        Args:
            max_count: Maximum number of commits to return.

        Returns:
            List of commit dicts with hash, author, date, subject.
        """
        try:
            output = self._git(
                "log",
                f"--max-count={max_count}",
                "--format=%H|%an|%ai|%s",
            )
            if not output:
                return []

            commits = []
            for line in output.split("\n"):
                if "|" in line:
                    parts = line.split("|", 3)
                    commits.append(
                        {
                            "hash": parts[0][:8],
                            "author": parts[1],
                            "date": parts[2],
                            "subject": parts[3] if len(parts) > 3 else "",
                        }
                    )
            return commits
        except RuntimeError:
            return []

    def get_diff(self, commit_hash: str) -> str:
        """Get the diff for a specific commit.

        Args:
            commit_hash: Commit hash to diff.

        Returns:
            Diff output.
        """
        try:
            return self._git("show", commit_hash, "--stat", "--no-patch")
        except RuntimeError:
            return ""

    def repository_size(self) -> str:
        """Get the repository size.

        Returns:
            Human-readable size string.
        """
        try:
            result = subprocess.run(
                ["du", "-sh", str(self.mail_dir / ".git")],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip().split()[0] if result.stdout else "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "unknown"
