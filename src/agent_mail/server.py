"""
HALF — Agent Mail: FastMCP Server

Exposes Agent Mail as MCP tools for agent coordination:
- send_message / get_messages / get_thread
- register_agent / list_agents
- acquire_lease / release_lease / get_active_leases
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from src.agent_mail.database import AgentMailDatabase
from src.agent_mail.models import MessageType

logger = logging.getLogger("half.agent_mail.server")

# Create the FastMCP server
mcp = FastMCP(
    "Agent Mail",
    dependencies=["mcp"],
)


# ─── Database Singleton ───────────────────────────────────────────────────────


_db: Optional[AgentMailDatabase] = None


def get_db() -> AgentMailDatabase:
    """Get or create the database singleton."""
    global _db
    if _db is None:
        db_path = Path(".hale/agent-mail/mail.db")
        _db = AgentMailDatabase(db_path)
    return _db


# ─── Agent Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
def register_agent(name: str, role: str = "unknown") -> dict[str, Any]:
    """Register a new agent in the mail system.

    Args:
        name: Agent name (becomes email: name@half.local).
        role: Agent role (coder, reviewer, security, etc.).

    Returns:
        Dict with agent email and registration status.
    """
    db = get_db()
    agent = db.register_agent(name=name, role=role)
    return {
        "status": "registered",
        "email": agent.email,
        "name": agent.name,
        "role": agent.role,
    }


@mcp.tool()
def list_agents() -> list[dict[str, Any]]:
    """List all registered agents in the mail system.

    Returns:
        List of agent dicts with email, name, and role.
    """
    db = get_db()
    agents = db.list_agents()
    return [
        {"email": a.email, "name": a.name, "role": a.role, "active": a.is_active}
        for a in agents
    ]


# ─── Message Tools ────────────────────────────────────────────────────────────


@mcp.tool()
def send_message(
    sender: str,
    recipients: str,
    subject: str,
    body: str,
    message_type: str = "direct",
    thread_id: str = "",
    in_reply_to: str = "",
) -> dict[str, Any]:
    """Send a message between agents.

    Args:
        sender: Sender email (agent@half.local).
        recipients: Comma-separated list of recipient emails.
        subject: Message subject line.
        body: Message body content.
        message_type: Message type (direct, broadcast, request_contact,
                      task_assignment, file_reservation, file_release, crp, ack).
        thread_id: Thread ID for grouping (auto-generated if empty).
        in_reply_to: Message ID being replied to.

    Returns:
        Dict with message ID and status.
    """
    db = get_db()

    try:
        msg_type = MessageType(message_type)
    except ValueError:
        msg_type = MessageType.DIRECT

    recipient_list = [r.strip() for r in recipients.split(",")]

    message = db.send_message(
        message_type=msg_type,
        sender=sender,
        recipients=recipient_list,
        subject=subject,
        body=body,
        thread_id=thread_id,
        in_reply_to=in_reply_to,
    )

    return {
        "status": "sent",
        "message_id": message.id,
        "thread_id": message.thread_id,
    }


@mcp.tool()
def get_messages(
    agent_email: str,
    limit: int = 50,
    unread_only: bool = False,
) -> list[dict[str, Any]]:
    """Get messages for an agent.

    Args:
        agent_email: Agent email to fetch messages for.
        limit: Maximum messages to return (default 50).
        unread_only: Only return unread messages (default false).

    Returns:
        List of message dicts.
    """
    db = get_db()
    messages = db.get_messages(agent_email, limit=limit, unread_only=unread_only)
    return [
        {
            "id": m.id,
            "type": m.message_type.value,
            "sender": m.sender,
            "recipients": m.recipients,
            "subject": m.subject,
            "body": m.body[:500],  # Truncate for MCP context
            "thread_id": m.thread_id,
            "created_at": m.created_at,
            "read": m.read,
        }
        for m in messages
    ]


@mcp.tool()
def mark_read(message_id: str) -> dict[str, Any]:
    """Mark a message as read.

    Args:
        message_id: The message ID to mark as read.

    Returns:
        Dict with status.
    """
    db = get_db()
    success = db.mark_read(message_id)
    return {"status": "marked_read" if success else "not_found"}


@mcp.tool()
def get_thread(thread_id: str) -> list[dict[str, Any]]:
    """Get all messages in a conversation thread.

    Args:
        thread_id: Thread ID to fetch.

    Returns:
        List of messages in the thread, ordered by time.
    """
    db = get_db()
    messages = db.get_thread(thread_id)
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "subject": m.subject,
            "body": m.body[:500],
            "created_at": m.created_at,
        }
        for m in messages
    ]


# ─── File Lease Tools ─────────────────────────────────────────────────────────


@mcp.tool()
def acquire_lease(
    file_path: str,
    agent_email: str,
    reason: str = "",
) -> dict[str, Any]:
    """Acquire a voluntary file reservation lease.

    Prevents other agents from modifying the same file concurrently.

    Args:
        file_path: Path of the file to reserve.
        agent_email: Agent email requesting the lease.
        reason: Why the file needs to be reserved.

    Returns:
        Dict with lease status and ID.
    """
    db = get_db()
    lease = db.acquire_lease(file_path=file_path, agent_email=agent_email, reason=reason)

    if lease is None:
        return {
            "status": "conflict",
            "message": f"File '{file_path}' is already leased by another agent",
        }

    return {
        "status": "acquired",
        "lease_id": lease.id,
        "file_path": lease.file_path,
        "agent": lease.agent_email,
    }


@mcp.tool()
def release_lease(lease_id: str, agent_email: str) -> dict[str, Any]:
    """Release a file reservation lease.

    Args:
        lease_id: Lease ID to release.
        agent_email: Agent email that owns the lease.

    Returns:
        Dict with release status.
    """
    db = get_db()
    success = db.release_lease(lease_id=lease_id, agent_email=agent_email)
    return {
        "status": "released" if success else "not_found_or_not_owner",
    }


@mcp.tool()
def get_active_leases(agent_email: str = "") -> list[dict[str, Any]]:
    """Get active file leases, optionally filtered by agent.

    Args:
        agent_email: Optional agent email to filter by.

    Returns:
        List of active lease dicts.
    """
    db = get_db()
    leases = db.get_active_leases(agent_email or None)
    return [
        {
            "id": l.id,
            "file_path": l.file_path,
            "agent": l.agent_email,
            "acquired_at": l.acquired_at,
            "reason": l.reason,
        }
        for l in leases
    ]


# ─── Server Entrypoint ────────────────────────────────────────────────────────


def run_server(host: str = "127.0.0.1", port: int = 9721) -> None:
    """Run the Agent Mail MCP server via SSE transport.

    Args:
        host: Host to bind to.
        port: Port to listen on.
    """
    logger.info("Starting Agent Mail server at http://%s:%d/mcp", host, port)
    mcp.run(transport="sse")


if __name__ == "__main__":
    run_server()
