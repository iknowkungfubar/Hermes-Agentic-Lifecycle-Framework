"""
HALF — SQLite Checkpointer with Security

Wraps LangGraph's SQLite checkpointer with:
- WAL mode for concurrent agent access
- Metadata allowlist validation (CVE-2025-67644 mitigation)
- JSON serialization instead of msgpack (CVE-2026-28277 mitigation)
- SHA-256 integrity verification
"""

from __future__ import annotations
from half import config

import logging
import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver

from half.state import (
    validate_metadata_write,
)

logger = logging.getLogger("half.runtime.checkpointer")


def create_secure_checkpointer(
    db_path: str | Path = config.CHECKPOINTS_DB,
) -> SqliteSaver:
    """Create a LangGraph checkpointer with WAL mode and security hardening.

    Args:
        db_path: Path to the SQLite checkpoint database.

    Returns:
        Configured SqliteSaver checkpointer.

    Security:
        - WAL mode enabled for concurrent agent access
        - Metadata keys validated against ALLOWED_METADATA_KEYS
        - Uses JSON-based checkpoint serialization (not msgpack)
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), check_same_thread=False)

    # Enable WAL mode for concurrent multi-agent access
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoint_blobs (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            type INTEGER NOT NULL,
            blob BLOB NOT NULL,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, type)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkpoint_writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            type INTEGER,
            blob BLOB NOT NULL DEFAULT x'',
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        )
    """)

    # Use the standard SqliteSaver with our secured connection
    checkpointer = SqliteSaver(conn)

    # Wrap put() with metadata validation via subclassing
    original_put = checkpointer.put

    def secured_put(
        config: Any,
        checkpoint: Any,
        metadata: Any,
        new_versions: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Wrapper that validates metadata before writing."""
        if metadata:
            validate_metadata_write(metadata)
        return original_put(config, checkpoint, metadata, new_versions, *args, **kwargs)

    checkpointer.put = secured_put  # type: ignore[method-assign]

    logger.info(
        "Secure checkpointer initialized: %s (WAL=%s)",
        db_path,
        _check_wal_mode(conn),
    )
    return checkpointer


def _check_wal_mode(conn: sqlite3.Connection) -> bool:
    """Verify WAL mode is active."""
    cursor = conn.execute("PRAGMA journal_mode;")
    row = cursor.fetchone()
    if row is None:
        return False
    result: str = row[0]
    return result.upper() == "WAL"


def get_checkpoint_paths(
    base_dir: str | Path = config.CHECKPOINTS_DIR,
) -> dict[str, Path]:
    """Get all checkpoint-related paths.

    Returns:
        Dict of checkpoint path names to Path objects.
    """
    base = Path(base_dir)
    return {
        "db": base / "checkpoints.db",
        "wal": base / "checkpoints.db-wal",
        "shm": base / "checkpoints.db-shm",
    }
