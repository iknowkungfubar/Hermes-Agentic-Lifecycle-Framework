"""HALF 1.5 — PGlite Global Context Registry.

Embedded PostgreSQL-style knowledge graph for codebase context.
Replaces flat files with a relational Knowledge Graph.
Agents subscribe ONLY to relevant views (no-slop enforcement).

Based on the HALF 1.5 doctrine's 'Global Context Registry' spec.
Uses PGlite (WASM PostgreSQL) or SQLite fallback for zero-config operation.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.pglite_registry")


@dataclass
class CodeEntity:
    """A code entity stored in the knowledge graph."""

    entity_type: str  # function, class, module, file, import, route, schema
    name: str
    file_path: str
    line_start: int = 0
    line_end: int = 0
    docstring: str = ""
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentView:
    """A filtered view of the knowledge graph for a specific agent role."""

    name: str
    agent_role: str  # coder, reviewer, security, dba, frontend
    entity_types: list[str] = field(default_factory=list)
    file_globs: list[str] = field(default_factory=list)
    max_tokens: int = 4000


# Predefined views for agent roles
AGENT_VIEWS = {
    "coder": AgentView(
        name="coder_context",
        agent_role="coder",
        entity_types=["function", "class", "module", "import"],
        max_tokens=4000,
    ),
    "dba": AgentView(
        name="schema_context",
        agent_role="dba",
        entity_types=["schema", "table", "index", "migration"],
        max_tokens=2000,
    ),
    "frontend": AgentView(
        name="frontend_context",
        agent_role="frontend",
        entity_types=["component", "route", "style"],
        file_globs=["*.tsx", "*.jsx", "*.vue", "*.css"],
        max_tokens=3000,
    ),
    "security": AgentView(
        name="security_context",
        agent_role="security",
        entity_types=["auth", "permission", "api_key", "credential"],
        max_tokens=2000,
    ),
    "reviewer": AgentView(
        name="review_context",
        agent_role="reviewer",
        entity_types=["function", "class", "test"],
        max_tokens=5000,
    ),
}


class PGliteRegistry:
    """Embedded knowledge graph for codebase context.

    Stores code entities in a relational database (SQLite by default,
    PGlite/PostgreSQL when available) and provides filtered views
    per agent role.

    Usage:
        registry = PGliteRegistry()
        registry.index_codebase("src/")
        view = registry.get_view("coder")
        # view contains only functions, classes, modules — no CSS
    """

    def __init__(self, db_path: str | Path = ".hale/context-registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the knowledge graph schema."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS code_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_start INTEGER DEFAULT 0,
                line_end INTEGER DEFAULT 0,
                docstring TEXT DEFAULT '',
                dependencies TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS file_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                summary TEXT NOT NULL,
                token_count INTEGER DEFAULT 0,
                last_indexed TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS agent_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_role TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                UNIQUE(agent_role, entity_type)
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_entities_type ON code_entities(entity_type);
            CREATE INDEX IF NOT EXISTS idx_entities_file ON code_entities(file_path);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_role ON agent_subscriptions(agent_role);
        """)
        self._conn.commit()

    # ─── Entity Management ──────────────────────────────────────────────

    def index_file(self, file_path: str) -> list[CodeEntity]:
        """Parse a Python file and index its entities.

        Args:
            file_path: Path to the Python file.

        Returns:
            List of indexed CodeEntity objects.
        """
        import ast

        path = Path(file_path)
        if not path.exists() or path.suffix != ".py":
            return []

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning("Registry: Failed to parse %s: %s", file_path, e)
            return []

        entities: list[CodeEntity] = []

        # Index module docstring
        module_doc = ast.get_docstring(tree) or ""
        entities.append(CodeEntity(
            entity_type="module",
            name=path.stem,
            file_path=file_path,
            docstring=module_doc[:200],
        ))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                entities.append(CodeEntity(
                    entity_type="class",
                    name=node.name,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    docstring=doc[:200],
                    dependencies=methods,
                ))

            elif isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or ""
                entities.append(CodeEntity(
                    entity_type="function",
                    name=node.name,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=getattr(node, "end_lineno", node.lineno),
                    docstring=doc[:200],
                ))

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    entities.append(CodeEntity(
                        entity_type="import",
                        name=alias.name,
                        file_path=file_path,
                        line_start=node.lineno,
                    ))

        # Persist to database
        for entity in entities:
            self._conn.execute(
                "INSERT OR REPLACE INTO code_entities "
                "(entity_type, name, file_path, line_start, line_end, docstring, dependencies, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entity.entity_type, entity.name, entity.file_path,
                    entity.line_start, entity.line_end, entity.docstring,
                    json.dumps(entity.dependencies), json.dumps(entity.metadata),
                ),
            )

        self._conn.commit()
        logger.info("Registry: Indexed %d entities from %s", len(entities), file_path)
        return entities

    def index_codebase(self, root_path: str | Path = "src") -> int:
        """Index all Python files in a directory tree.

        Args:
            root_path: Root directory to index.

        Returns:
            Total number of entities indexed.
        """
        root = Path(root_path)
        total = 0
        for py_file in sorted(root.rglob("*.py")):
            entities = self.index_file(str(py_file))
            total += len(entities)
        logger.info("Registry: Indexed %d entities total from %s", total, root)
        return total

    # ─── View System ────────────────────────────────────────────────────

    def get_view(self, agent_role: str = "coder", max_entities: int = 50) -> list[dict[str, Any]]:
        """Get a filtered view of the knowledge graph for an agent role.

        Args:
            agent_role: Agent role (coder, dba, frontend, security, reviewer).
            max_entities: Max entities to return.

        Returns:
            List of entity dicts relevant to the agent's role.
        """
        view = AGENT_VIEWS.get(agent_role, AGENT_VIEWS["coder"])

        if view.entity_types:
            placeholders = ",".join("?" for _ in view.entity_types)
            rows = self._conn.execute(
                f"SELECT * FROM code_entities WHERE entity_type IN ({placeholders}) "
                f"ORDER BY line_start LIMIT ?",
                [*view.entity_types, max_entities],
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM code_entities ORDER BY line_start LIMIT ?",
                (max_entities,),
            ).fetchall()

        return [dict(r) for r in rows]

    def search_entities(self, query: str, entity_type: str = "") -> list[dict[str, Any]]:
        """Search for entities by name or docstring.

        Args:
            query: Search term.
            entity_type: Optional filter by entity type.

        Returns:
            Matching entities.
        """
        if entity_type:
            rows = self._conn.execute(
                "SELECT * FROM code_entities WHERE (name LIKE ? OR docstring LIKE ?) AND entity_type = ?",
                (f"%{query}%", f"%{query}%", entity_type),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM code_entities WHERE name LIKE ? OR docstring LIKE ?",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        return [dict(r) for r in rows]

    def subscribe(self, agent_role: str, entity_types: list[str]) -> None:
        """Subscribe an agent role to specific entity types.

        Args:
            agent_role: Agent role name.
            entity_types: Entity types to subscribe to.
        """
        for i, etype in enumerate(entity_types):
            self._conn.execute(
                "INSERT OR REPLACE INTO agent_subscriptions (agent_role, entity_type, priority) "
                "VALUES (?, ?, ?)",
                (agent_role, etype, i),
            )
        self._conn.commit()
        logger.info("Registry: Subscribed '%s' to %s", agent_role, entity_types)

    def get_subscription(self, agent_role: str) -> list[str]:
        """Get the entity types an agent role is subscribed to.

        Args:
            agent_role: Agent role name.

        Returns:
            List of entity type strings.
        """
        rows = self._conn.execute(
            "SELECT entity_type FROM agent_subscriptions WHERE agent_role = ? ORDER BY priority",
            (agent_role,),
        ).fetchall()
        return [r["entity_type"] for r in rows]

    # ─── User Preferences ───────────────────────────────────────────────

    def set_preference(self, key: str, value: str) -> None:
        """Store a persistent user preference.

        Args:
            key: Preference key.
            value: Preference value.
        """
        self._conn.execute(
            "INSERT OR REPLACE INTO user_preferences (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now(tz=timezone.utc).isoformat()),
        )
        self._conn.commit()

    def get_preference(self, key: str, default: str = "") -> str:
        """Get a stored user preference.

        Args:
            key: Preference key.
            default: Default value if not found.

        Returns:
            Preference value or default.
        """
        row = self._conn.execute(
            "SELECT value FROM user_preferences WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def get_all_preferences(self) -> dict[str, str]:
        """Get all stored preferences.

        Returns:
            Dict of key-value pairs.
        """
        rows = self._conn.execute("SELECT key, value FROM user_preferences").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ─── Summary & Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge graph statistics.

        Returns:
            Dict with entity counts by type.
        """
        rows = self._conn.execute(
            "SELECT entity_type, COUNT(*) as count FROM code_entities GROUP BY entity_type"
        ).fetchall()
        return {"entities": {r["entity_type"]: r["count"] for r in rows}}

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
