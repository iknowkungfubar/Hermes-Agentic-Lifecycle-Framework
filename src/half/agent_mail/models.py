"""
HALF — Agent Mail: Data Models

Agent identities, messages, and file reservation leases
for decentralized multi-agent coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum


class MessageType(Enum):
    """Types of messages agents can exchange."""

    DIRECT = "direct"  # One-to-one message
    BROADCAST = "broadcast"  # All agents
    REQUEST_CONTACT = "request_contact"  # Handshake
    TASK_ASSIGNMENT = "task_assignment"  # Assign a task
    FILE_RESERVATION = "file_reservation"  # Reserve a file
    FILE_RELEASE = "file_release"  # Release a file reservation
    CRP = "crp"  # Consultation Request Pack
    ACK = "ack"  # Acknowledgment


class LeaseStatus(Enum):
    """Status of a file reservation lease."""

    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"
    CONTESTED = "contested"


@dataclass
class Agent:
    """An agent identity in the mail system."""

    email: str  # agent_name@half.local
    name: str
    role: str  # coder, reviewer, security, etc.
    public_key: str = ""
    is_active: bool = True
    registered_at: str = ""


@dataclass
class Message:
    """A message between agents."""

    id: str
    message_type: MessageType
    sender: str  # Agent email
    recipients: list[str]  # List of agent emails
    subject: str
    body: str
    thread_id: str = ""
    in_reply_to: str = ""
    attachments: list[str] = field(default_factory=list)
    created_at: str = ""
    read: bool = False
    read_at: str = ""


@dataclass
class FileLease:
    """A voluntary file reservation lease.

    Agents register a lease on a file they intend to modify,
    preventing other agents from making conflicting changes.
    """

    id: str
    file_path: str
    agent_email: str
    status: LeaseStatus = LeaseStatus.ACTIVE
    acquired_at: str = ""
    expires_at: str = ""
    released_at: str = ""
    reason: str = ""


# ─── Helpers ──────────────────────────────────────────────────────────────────


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(tz=UTC).isoformat()


def default_expiry(hours: int = 2) -> str:
    """Get a default lease expiry timestamp.

    Args:
        hours: Hours from now until expiry.

    Returns:
        ISO-format expiry timestamp.
    """
    return (datetime.now(tz=UTC) + timedelta(hours=hours)).isoformat()


def make_email(agent_name: str) -> str:
    """Create an agent email address."""
    return f"{agent_name}@half.local"
