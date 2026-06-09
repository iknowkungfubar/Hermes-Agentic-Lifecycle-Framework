"""
HALF — Agent Mail

Decentralized agent coordination layer:
- Email-like messaging between agents
- File reservation leases to prevent concurrent writes
- SQLite-backed with WAL mode
- Exposed as MCP server for Hermes tool integration
"""

from __future__ import annotations

from src.agent_mail.database import AgentMailDatabase
from src.agent_mail.models import (
    Agent,
    FileLease,
    LeaseStatus,
    Message,
    MessageType,
    make_email,
)
from src.agent_mail.server import mcp, run_server

__all__ = [
    "Agent",
    "AgentMailDatabase",
    "FileLease",
    "LeaseStatus",
    "Message",
    "MessageType",
    "make_email",
    "mcp",
    "run_server",
]
