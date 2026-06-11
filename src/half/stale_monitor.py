"""HALF — Stale Session Monitor.

Background daemon that continuously scans the Kanban boards and execution
layers to detect and prune deadlocked agent operations, orphan files,
and stale work sessions.

Based on the HALF doctrine's PDA capabilities.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.stale_monitor")


@dataclass
class StaleSession:
    """A detected stale session."""

    type: str  # agent, file, git_branch, checkpoint
    name: str
    age_hours: float
    path: str = ""
    action: str = ""  # prune, warn, ignore


class StaleSessionMonitor:
    """Monitors for deadlocked agents, orphan files, and stale sessions.

    Designed to run as a background daemon (thread or cron job) that:
    1. Scans agent checkpoint directories for stale state
    2. Detects orphan Git branches
    3. Finds temp/artifact files past their TTL
    4. Reports deadlocked agent mail threads
    """

    def __init__(
        self,
        repo_path: str | Path = ".",
        max_agent_age_hours: float = 24.0,
        max_branch_age_days: float = 14.0,
        max_file_age_hours: float = 48.0,
    ):
        self.repo_path = Path(repo_path)
        self.max_agent_age = max_agent_age_hours
        self.max_branch_age = max_branch_age_days
        self.max_file_age = max_file_age_hours
        self.sessions: list[StaleSession] = []

    def scan(self) -> list[StaleSession]:
        """Scan for all stale sessions.

        Returns:
            List of detected stale sessions.
        """
        self.sessions = []
        now = datetime.now(tz=timezone.utc)

        self._scan_checkpoints(now)
        self._scan_git_branches(now)
        self._scan_artifacts(now)
        self._scan_agent_mail(now)

        if self.sessions:
            logger.info("Stale Monitor: Found %d stale sessions", len(self.sessions))
        else:
            logger.info("Stale Monitor: No stale sessions detected")

        return self.sessions

    def _scan_checkpoints(self, now: datetime) -> None:
        """Scan LangGraph checkpoint directory for stale state."""
        ckpt_dir = self.repo_path / ".hale" / "state" / "checkpoints"
        if not ckpt_dir.exists():
            return

        for f in ckpt_dir.iterdir():
            if f.suffix == ".json":
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                age = (now - mtime).total_seconds() / 3600
                if age > self.max_agent_age:
                    self.sessions.append(StaleSession(
                        type="checkpoint",
                        name=f.name,
                        age_hours=age,
                        path=str(f),
                        action="prune" if age > self.max_agent_age * 2 else "warn",
                    ))

    def _scan_git_branches(self, now: datetime) -> None:
        """Scan for stale Git branches."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "branch", "-r"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.repo_path),
            )
            for line in result.stdout.split("\n"):
                branch = line.strip().replace("*", "").strip()
                if not branch or branch in ("origin/master", "origin/main", "origin/HEAD"):
                    continue
                # Get branch age
                age_result = subprocess.run(
                    ["git", "log", "-1", "--format=%ci", branch],
                    capture_output=True, text=True, timeout=15,
                    cwd=str(self.repo_path),
                )
                if age_result.stdout:
                    try:
                        branch_time = datetime.strptime(
                            age_result.stdout.strip(), "%Y-%m-%d %H:%M:%S %z"
                        )
                        age = (now - branch_time).total_seconds() / 86400
                        if age > self.max_branch_age:
                            self.sessions.append(StaleSession(
                                type="git_branch",
                                name=branch,
                                age_hours=age * 24,
                                action="warn",
                            ))
                    except ValueError:
                        continue
        except Exception:
            pass

    def _scan_artifacts(self, now: datetime) -> None:
        """Scan for stale artifact files."""
        artifacts_dir = self.repo_path / ".hale" / "artifacts"
        if not artifacts_dir.exists():
            return

        for f in artifacts_dir.rglob("*"):
            if f.is_file() and f.suffix not in (".gitkeep",):
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                age = (now - mtime).total_seconds() / 3600
                if age > self.max_file_age:
                    self.sessions.append(StaleSession(
                        type="artifact",
                        name=str(f.relative_to(artifacts_dir)),
                        age_hours=age,
                        path=str(f),
                        action="prune" if age > self.max_file_age * 2 else "warn",
                    ))

    def _scan_agent_mail(self, now: datetime) -> None:
        """Scan Agent Mail for stalled conversations."""
        mail_dir = self.repo_path / ".hale" / "agent-mail"
        if not mail_dir.exists():
            return
        db_file = mail_dir / "mail.db"
        if not db_file.exists():
            return

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.execute(
                "SELECT thread_id, MAX(created_at) as last_msg, COUNT(*) as count "
                "FROM messages GROUP BY thread_id HAVING count > 5"
            )
            for row in cursor.fetchall():
                thread_id, last_msg, count = row
                try:
                    msg_time = datetime.fromisoformat(last_msg)
                    age = (now - msg_time.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                    if age > 4:  # Threads stalled for >4 hours
                        self.sessions.append(StaleSession(
                            type="agent_mail_thread",
                            name=f"thread-{thread_id[:8]}",
                            age_hours=age,
                            action="warn",
                        ))
                except (ValueError, TypeError):
                    continue
            conn.close()
        except Exception:
            pass

    def prune(self, session: StaleSession) -> bool:
        """Prune a stale session.

        Args:
            session: The session to prune.

        Returns:
            True if successfully pruned.
        """
        try:
            if session.type == "checkpoint" and session.path:
                os.remove(session.path)
                logger.info("Pruned checkpoint: %s", session.name)
                return True
            elif session.type == "artifact" and session.path:
                os.remove(session.path)
                logger.info("Pruned artifact: %s", session.name)
                return True
            elif session.type == "git_branch":
                import subprocess
                subprocess.run(
                    ["git", "branch", "-d", session.name],
                    capture_output=True, text=True, timeout=15,
                    cwd=str(self.repo_path),
                )
                logger.info("Pruned branch: %s", session.name)
                return True
            return False
        except Exception as e:
            logger.warning("Failed to prune %s: %s", session.name, e)
            return False
