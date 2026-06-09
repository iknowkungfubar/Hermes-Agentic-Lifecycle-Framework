"""Tests for Agent Mail system."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.agent_mail.database import AgentMailDatabase
from src.agent_mail.models import MessageType


@pytest.fixture
def db():
    """Create a temporary Agent Mail database for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test_mail.db"
        database = AgentMailDatabase(db_path)
        yield database
        database.close()


class TestAgentRegistration:
    """Test agent registration operations."""

    def test_register_agent(self, db):
        """Registering an agent should return an agent with email."""
        agent = db.register_agent(name="coder-1", role="coder")
        assert agent.email == "coder-1@half.local"
        assert agent.name == "coder-1"
        assert agent.role == "coder"
        assert agent.is_active is True

    def test_register_duplicate(self, db):
        """Registering the same agent twice should not raise."""
        db.register_agent(name="coder-1", role="coder")
        db.register_agent(name="coder-1", role="coder")  # No error
        agents = db.list_agents()
        assert len(agents) == 1  # Only one copy

    def test_get_agent(self, db):
        """Getting an agent by email should return the agent."""
        db.register_agent(name="reviewer-1", role="reviewer")
        agent = db.get_agent("reviewer-1@half.local")
        assert agent is not None
        assert agent.role == "reviewer"

    def test_get_nonexistent_agent(self, db):
        """Getting a nonexistent agent should return None."""
        agent = db.get_agent("nobody@half.local")
        assert agent is None

    def test_list_agents(self, db):
        """Listing agents should return all registered agents."""
        db.register_agent(name="a1", role="coder")
        db.register_agent(name="a2", role="reviewer")
        db.register_agent(name="a3", role="security")
        agents = db.list_agents()
        assert len(agents) == 3


class TestMessaging:
    """Test messaging operations."""

    def test_send_message(self, db):
        """Sending a message should return a message with id."""
        db.register_agent(name="alice", role="coder")
        db.register_agent(name="bob", role="reviewer")

        msg = db.send_message(
            message_type=MessageType.DIRECT,
            sender="alice@half.local",
            recipients=["bob@half.local"],
            subject="Review needed",
            body="Please review PR #42",
        )
        assert msg.id is not None
        assert msg.sender == "alice@half.local"
        assert msg.subject == "Review needed"

    def test_get_messages(self, db):
        """Getting messages should return received messages."""
        db.register_agent(name="alice", role="coder")
        db.register_agent(name="bob", role="reviewer")

        db.send_message(
            MessageType.DIRECT,
            "alice@half.local",
            ["bob@half.local"],
            "Test",
            "Hello Bob",
        )
        messages = db.get_messages("bob@half.local")
        assert len(messages) == 1
        assert messages[0].sender == "alice@half.local"

    def test_unread_messages(self, db):
        """Getting unread messages should only return unread ones."""
        db.register_agent(name="alice", role="coder")
        db.register_agent(name="bob", role="reviewer")

        db.send_message(
            MessageType.DIRECT,
            "alice@half.local",
            ["bob@half.local"],
            "Urgent",
            "Fix this bug!",
        )

        unread = db.get_messages("bob@half.local", unread_only=True)
        assert len(unread) == 1

        # Mark as read
        db.mark_read(unread[0].id)
        unread = db.get_messages("bob@half.local", unread_only=True)
        assert len(unread) == 0

    def test_thread(self, db):
        """Getting a thread should return all messages in it."""
        db.register_agent(name="alice", role="coder")
        db.register_agent(name="bob", role="reviewer")

        msg1 = db.send_message(
            MessageType.DIRECT,
            "alice@half.local",
            ["bob@half.local"],
            "Thread start",
            "Message 1",
        )
        db.send_message(
            MessageType.DIRECT,
            "bob@half.local",
            ["alice@half.local"],
            "Re: Thread start",
            "Message 2",
            thread_id=msg1.thread_id,
            in_reply_to=msg1.id,
        )

        thread = db.get_thread(msg1.thread_id)
        assert len(thread) == 2


class TestFileLeases:
    """Test file reservation lease operations."""

    def test_acquire_lease(self, db):
        """Acquiring a lease should return a lease with id."""
        db.register_agent(name="coder-1", role="coder")
        lease = db.acquire_lease(
            file_path="src/main.py",
            agent_email="coder-1@half.local",
            reason="Refactoring main module",
        )
        assert lease is not None
        assert lease.file_path == "src/main.py"
        assert lease.agent_email == "coder-1@half.local"

    def test_acquire_conflict(self, db):
        """Acquiring an already-leased file should return None."""
        db.register_agent(name="a1", role="coder")
        db.register_agent(name="a2", role="coder")

        db.acquire_lease("src/main.py", "a1@half.local")
        conflict = db.acquire_lease("src/main.py", "a2@half.local")
        assert conflict is None

    def test_release_lease(self, db):
        """Releasing a lease should succeed for the owner."""
        db.register_agent(name="coder-1", role="coder")
        lease = db.acquire_lease("src/main.py", "coder-1@half.local")
        assert lease is not None

        result = db.release_lease(lease.id, "coder-1@half.local")
        assert result is True

    def test_release_wrong_owner(self, db):
        """Releasing another agent's lease should fail."""
        db.register_agent(name="a1", role="coder")
        db.register_agent(name="a2", role="coder")

        lease = db.acquire_lease("src/main.py", "a1@half.local")
        assert lease is not None

        result = db.release_lease(lease.id, "a2@half.local")
        assert result is False

    def test_get_active_leases(self, db):
        """Getting active leases should return them."""
        db.register_agent(name="a1", role="coder")
        db.register_agent(name="a2", role="coder")

        db.acquire_lease("src/a.py", "a1@half.local")
        db.acquire_lease("src/b.py", "a2@half.local")

        leases = db.get_active_leases()
        assert len(leases) == 2

    def test_get_active_leases_filtered(self, db):
        """Getting active leases filtered by agent."""
        db.register_agent(name="a1", role="coder")
        db.register_agent(name="a2", role="coder")

        db.acquire_lease("src/a.py", "a1@half.local")
        db.acquire_lease("src/b.py", "a2@half.local")

        leases = db.get_active_leases(agent_email="a1@half.local")
        assert len(leases) == 1
        assert leases[0].file_path == "src/a.py"
