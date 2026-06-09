"""
HALF — Agent Mail: SQLite Database Layer

Backed by SQLite with WAL mode for concurrent multi-agent writes.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from half.agent_mail.git_backend import GitMailBackend
from half.agent_mail.models import (
    Agent,
    FileLease,
    LeaseStatus,
    Message,
    MessageType,
    now_iso,
)
from half import config


class AgentMailDatabase:
    """SQLite-backed persistent store for Agent Mail.

    Backed by Git for full audit trail and decentralized backup.
    """

    def __init__(
        self, db_path: str | Path = config.AGENT_MAIL_DB, enable_git: bool = True
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        # Enable WAL for concurrent multi-agent access
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA busy_timeout=5000;")

        # Initialize Git backend for audit trail
        self._git: GitMailBackend | None = None
        if enable_git:
            try:
                self._git = GitMailBackend(mail_dir=self.db_path.parent)
            except Exception as e:
                import logging

                logging.getLogger("half.agent_mail").warning(
                    "Git backend disabled: %s", e
                )

        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'unknown',
                public_key TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                registered_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                message_type TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipients TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                thread_id TEXT DEFAULT '',
                in_reply_to TEXT DEFAULT '',
                attachments TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                read_at TEXT DEFAULT NULL,
                FOREIGN KEY (sender) REFERENCES agents(email)
            );

            CREATE TABLE IF NOT EXISTS file_leases (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                agent_email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                acquired_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                released_at TEXT DEFAULT NULL,
                reason TEXT DEFAULT '',
                FOREIGN KEY (agent_email) REFERENCES agents(email)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_recipient
                ON messages(recipients);
            CREATE INDEX IF NOT EXISTS idx_messages_thread
                ON messages(thread_id);
            CREATE INDEX IF NOT EXISTS idx_file_leases_path
                ON file_leases(file_path);
            CREATE INDEX IF NOT EXISTS idx_file_leases_agent
                ON file_leases(agent_email);
        """)
        self._conn.commit()

    # ─── Agent Operations ──────────────────────────────────────────────────

    def register_agent(self, name: str, role: str = "unknown") -> Agent:
        """Register a new agent identity.

        Args:
            name: Agent name (becomes email: name@half.local).
            role: Agent role (e.g., coder, reviewer, security).

        Returns:
            The registered Agent.
        """
        email = f"{name}@half.local"
        now = now_iso()
        agent = Agent(email=email, name=name, role=role, registered_at=now)

        self._conn.execute(
            "INSERT OR IGNORE INTO agents (email, name, role, is_active, registered_at) "
            "VALUES (?, ?, ?, 1, ?)",
            (email, name, role, now),
        )
        self._conn.commit()

        # Git audit trail
        if self._git:
            self._git.commit_agent_registered(email, role)

        return agent

    def get_agent(self, email: str) -> Agent | None:
        """Get an agent by email.

        Args:
            email: Agent email address.

        Returns:
            Agent if found, None otherwise.
        """
        row = self._conn.execute(
            "SELECT * FROM agents WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return None
        return Agent(
            email=row["email"],
            name=row["name"],
            role=row["role"],
            public_key=row["public_key"],
            is_active=bool(row["is_active"]),
            registered_at=row["registered_at"],
        )

    def list_agents(self) -> list[Agent]:
        """List all registered agents.

        Returns:
            List of all agents.
        """
        rows = self._conn.execute(
            "SELECT * FROM agents ORDER BY registered_at"
        ).fetchall()
        return [
            Agent(
                email=r["email"],
                name=r["name"],
                role=r["role"],
                public_key=r["public_key"],
                is_active=bool(r["is_active"]),
                registered_at=r["registered_at"],
            )
            for r in rows
        ]

    # ─── Message Operations ────────────────────────────────────────────────

    def send_message(
        self,
        message_type: MessageType,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
        thread_id: str = "",
        in_reply_to: str = "",
    ) -> Message:
        """Send a message.

        Args:
            message_type: Type of message.
            sender: Sender email.
            recipients: List of recipient emails.
            subject: Message subject.
            body: Message body.
            thread_id: Optional thread ID for grouping.
            in_reply_to: Optional message ID being replied to.

        Returns:
            The sent Message.
        """
        msg_id = str(uuid.uuid4())[:12]
        now = now_iso()

        message = Message(
            id=msg_id,
            message_type=message_type,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            thread_id=thread_id or msg_id,
            in_reply_to=in_reply_to,
            created_at=now,
        )

        self._conn.execute(
            "INSERT INTO messages (id, message_type, sender, recipients, subject, "
            "body, thread_id, in_reply_to, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg_id,
                message_type.value,
                sender,
                ",".join(recipients),
                subject,
                body,
                message.thread_id,
                in_reply_to,
                now,
            ),
        )
        self._conn.commit()

        # Git audit trail
        if self._git:
            self._git.commit_message_sent(msg_id, sender, recipients)

        return message

    def get_messages(
        self,
        agent_email: str,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[Message]:
        """Get messages for an agent.

        Args:
            agent_email: Agent email to get messages for.
            limit: Max messages to return.
            unread_only: Only return unread messages.

        Returns:
            List of messages.
        """
        query = "SELECT * FROM messages WHERE recipients LIKE ?"
        params: list[Any] = [f"%{agent_email}%"]

        if unread_only:
            query += " AND read = 0"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_message(r) for r in rows]

    def mark_read(self, message_id: str) -> bool:
        """Mark a message as read.

        Args:
            message_id: Message ID to mark.

        Returns:
            True if message was found and marked.
        """
        cursor = self._conn.execute(
            "UPDATE messages SET read = 1, read_at = ? WHERE id = ?",
            (now_iso(), message_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def get_thread(self, thread_id: str) -> list[Message]:
        """Get all messages in a thread.

        Args:
            thread_id: Thread ID.

        Returns:
            List of messages in the thread.
        """
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at",
            (thread_id,),
        ).fetchall()
        return [self._row_to_message(r) for r in rows]

    # ─── File Lease Operations ─────────────────────────────────────────────

    def acquire_lease(
        self,
        file_path: str,
        agent_email: str,
        reason: str = "",
        expiry_hours: int = 2,
    ) -> FileLease | None:
        """Acquire a file reservation lease.

        Args:
            file_path: Path of the file to reserve.
            agent_email: Agent requesting the lease.
            reason: Reason for the lease.
            expiry_hours: Hours until lease expires.

        Returns:
            FileLease if acquired, None if already leased.
        """
        # Check for existing active lease
        existing = self._conn.execute(
            "SELECT * FROM file_leases WHERE file_path = ? AND status = 'active'",
            (file_path,),
        ).fetchone()

        if existing is not None:
            return None  # File is already leased

        lease_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expiry_hours)
        now_str = now.isoformat()
        expires_str = expires_at.isoformat()

        self._conn.execute(
            "INSERT INTO file_leases (id, file_path, agent_email, status, acquired_at, expires_at, reason) "
            "VALUES (?, ?, ?, 'active', ?, ?, ?)",
            (lease_id, file_path, agent_email, now_str, expires_str, reason),
        )
        self._conn.commit()

        # Git audit trail
        if self._git:
            self._git.commit_lease_acquired(lease_id, file_path, agent_email)

        return FileLease(
            id=lease_id,
            file_path=file_path,
            agent_email=agent_email,
            status=LeaseStatus.ACTIVE,
            acquired_at=now_str,
            expires_at=expires_str,
            reason=reason,
        )

    def release_lease(self, lease_id: str, agent_email: str) -> bool:
        """Release a file reservation lease.

        Args:
            lease_id: Lease ID to release.
            agent_email: Agent releasing (must match lease owner).

        Returns:
            True if released, False if not found or wrong owner.
        """
        cursor = self._conn.execute(
            "UPDATE file_leases SET status = 'released', released_at = ? "
            "WHERE id = ? AND agent_email = ? AND status = 'active'",
            (now_iso(), lease_id, agent_email),
        )
        self._conn.commit()

        # Git audit trail
        if self._git and cursor.rowcount > 0:
            file_path = self._conn.execute(
                "SELECT file_path FROM file_leases WHERE id = ?", (lease_id,)
            ).fetchone()
            if file_path:
                self._git.commit_lease_released(
                    lease_id, file_path["file_path"], agent_email
                )

        return cursor.rowcount > 0

    def get_active_leases(self, agent_email: str | None = None) -> list[FileLease]:
        """Get active leases, optionally filtered by agent.

        Args:
            agent_email: Optional filter by agent.

        Returns:
            List of active FileLeases.
        """
        if agent_email:
            rows = self._conn.execute(
                "SELECT * FROM file_leases WHERE status = 'active' AND agent_email = ?",
                (agent_email,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM file_leases WHERE status = 'active'"
            ).fetchall()

        return [
            FileLease(
                id=r["id"],
                file_path=r["file_path"],
                agent_email=r["agent_email"],
                status=LeaseStatus(r["status"]),
                acquired_at=r["acquired_at"],
                expires_at=r["expires_at"],
                reason=r["reason"],
            )
            for r in rows
        ]

    # ─── Internal ──────────────────────────────────────────────────────────

    def _row_to_message(self, row: sqlite3.Row) -> Message:
        return Message(
            id=row["id"],
            message_type=MessageType(row["message_type"]),
            sender=row["sender"],
            recipients=row["recipients"].split(","),
            subject=row["subject"],
            body=row["body"],
            thread_id=row["thread_id"],
            in_reply_to=row["in_reply_to"],
            created_at=row["created_at"],
            read=bool(row["read"]),
            read_at=row["read_at"] or "",
        )

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
