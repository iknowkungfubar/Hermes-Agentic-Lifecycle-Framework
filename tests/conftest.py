"""HALF — Shared Test Fixtures and Configuration."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_half_home() -> str:
    """Create a temporary HALF_HOME directory for testing.

    Sets HALF_HOME env var and restores original on teardown.
    """
    original = os.environ.get("HALF_HOME")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HALF_HOME"] = str(Path(tmp) / ".hale")
        yield str(Path(tmp) / ".hale")
    if original:
        os.environ["HALF_HOME"] = original
    else:
        os.environ.pop("HALF_HOME", None)


@pytest.fixture
def temp_cwd() -> str:
    """Temporarily change to a temp directory, restore on teardown."""
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        yield tmp
    os.chdir(str(original))


@pytest.fixture(autouse=True)
def _cleanup_db_after_test() -> None:
    """Clean up AgentMailDatabase singleton after each test."""
    yield
    try:
        from half.agent_mail.database import cleanup_db
        cleanup_db()
    except ImportError:
        pass
    try:
        from half.runtime.checkpointer import close_checkpointer
        # Close any open checkpointers — stored in module state
        import half.runtime.graph as graph_mod
        if hasattr(graph_mod, '_checkpointers'):
            for cp in graph_mod._checkpointers:
                close_checkpointer(cp)
            graph_mod._checkpointers = []
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def half_config_initialized(tmp_half_home: str) -> str:
    """Initialize HALF config directories in a temp location.

    Returns the HALF_HOME path.
    """
    from half.config import ensure_dirs
    ensure_dirs()
    return tmp_half_home
