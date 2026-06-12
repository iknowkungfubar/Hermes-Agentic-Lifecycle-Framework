"""HALF 1.5 — Environment Bootstrapping.

Injects a complete snapshot of the working directory and memory into the
prompt BEFORE the loop starts, saving 2-5 early exploration turns per task.

Based on the HALF 1.5 doctrine's 'Environment Bootstrapping' specification.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.env_bootstrap")


@dataclass
class BootstrapSnapshot:
    """A snapshot of the environment before execution."""

    project_name: str
    task: str
    directory_tree: str  # ASCII tree of relevant files
    key_files: dict[str, str] = field(default_factory=dict)  # filename -> first 50 lines
    recent_git_history: list[str] = field(default_factory=list)
    dependency_summary: str = ""
    active_agents: list[str] = field(default_factory=list)
    memory_snapshot: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


class EnvironmentBootstrapper:
    """Captures environment state and injects it into the agent's context.

    Saves 2-5 early exploration turns by providing the agent with a ready-made
    understanding of the project structure, key files, and current state.

    Usage:
        bootstrapper = EnvironmentBootstrapper()
        snapshot = bootstrapper.capture_snapshot("Implement user auth")
        prompt = bootstrapper.build_bootstrap_prompt(snapshot)
        # prompt contains everything the agent needs to start working
    """

    def __init__(self, root_path: str | Path = "."):
        self.root_path = Path(root_path)

    def capture_snapshot(self, task: str, project_name: str = "") -> BootstrapSnapshot:
        """Capture a complete environment snapshot.

        Args:
            task: The task about to be executed.
            project_name: Optional project name.

        Returns:
            BootstrapSnapshot with directory tree, key files, git state.
        """
        logger.info("Bootstrap: Capturing environment snapshot for '%s'", task[:60])

        snapshot = BootstrapSnapshot(
            project_name=project_name or self.root_path.name,
            task=task,
            directory_tree="",
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

        self._capture_directory_tree(snapshot)
        self._capture_key_files(snapshot)
        self._capture_git_history(snapshot)
        self._capture_dependencies(snapshot)
        self._capture_memory(snapshot)

        logger.info("Bootstrap: Captured %d key files, %d git entries",
                     len(snapshot.key_files), len(snapshot.recent_git_history))
        return snapshot

    def _capture_directory_tree(self, snapshot: BootstrapSnapshot) -> None:
        """Generate an ASCII directory tree for the project."""
        parts: list[str] = [f"{snapshot.project_name}/"]

        def _scan(dirpath: Path, prefix: str = "", depth: int = 0) -> None:
            if depth > 4:
                return
            entries = sorted(dirpath.iterdir())
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                if entry.name.startswith((".", "__", "node_modules", ".venv")):
                    continue
                connector = "└── " if is_last else "├── "
                parts.append(f"{prefix}{connector}{entry.name}")
                if entry.is_dir():
                    ext = "    " if is_last else "│   "
                    _scan(entry, prefix + ext, depth + 1)

        _scan(self.root_path)
        snapshot.directory_tree = "\n".join(parts)

    def _capture_key_files(self, snapshot: BootstrapSnapshot) -> None:
        """Capture the most important project files."""
        # Always capture these key files
        key_files_to_read = [
            "AGENTS.md", "README.md", ".goal/config.yaml",
            "pyproject.toml", "SKILL.md", "CHANGELOG.md",
        ]
        for fname in key_files_to_read:
            fpath = self.root_path / fname
            if fpath.exists():
                try:
                    content = fpath.read_text(encoding="utf-8")
                    snapshot.key_files[fname] = content[:2000]
                except Exception:
                    continue

    def _capture_git_history(self, snapshot: BootstrapSnapshot) -> None:
        """Capture recent git commit history."""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-20"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.root_path),
            )
            if result.stdout:
                snapshot.recent_git_history = [
                    l.strip() for l in result.stdout.split("\n") if l.strip()
                ]
        except Exception:
            pass

    def _capture_dependencies(self, snapshot: BootstrapSnapshot) -> None:
        """Capture project dependency summary."""
        import subprocess
        try:
            result = subprocess.run(
                ["uv", "pip", "list", "--format=columns"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.root_path),
            )
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                snapshot.dependency_summary = "\n".join(lines[:15])
        except Exception:
            try:
                result = subprocess.run(
                    ["python3", "-m", "pip", "list", "--format=columns"],
                    capture_output=True, text=True, timeout=15,
                    cwd=str(self.root_path),
                )
                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    snapshot.dependency_summary = "\n".join(lines[:15])
            except Exception:
                pass

    def _capture_memory(self, snapshot: BootstrapSnapshot) -> None:
        """Capture stored user preferences and memory state."""
        try:
            registry_path = self.root_path / ".hale" / "context-registry.db"
            if registry_path.exists():
                import sqlite3
                conn = sqlite3.connect(str(registry_path))
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT key, value FROM user_preferences"
                ).fetchall()
                snapshot.memory_snapshot = {r["key"]: r["value"] for r in rows}
                conn.close()
        except Exception:
            pass

    def build_bootstrap_prompt(self, snapshot: BootstrapSnapshot) -> str:
        """Build a bootstrap prompt string for injection into agent context.

        Args:
            snapshot: The environment snapshot.

        Returns:
            A string that can be injected as the system prompt.
        """
        lines = [
            "# Environment Bootstrap — Project Snapshot",
            "",
            f"## Project: {snapshot.project_name}",
            f"**Task:** {snapshot.task}",
            f"**Snapshot time:** {snapshot.timestamp}",
            "",
            "## Directory Structure",
            "```",
            snapshot.directory_tree[:1000],
            "```",
            "",
        ]

        if snapshot.key_files:
            lines.append("## Key Files")
            for name, content in snapshot.key_files.items():
                lines.extend(["", f"### {name}", "```", content[:500], "```"])

        if snapshot.recent_git_history:
            lines.extend(["", "## Recent Git History", "```"])
            lines.extend(snapshot.recent_git_history[:10])
            lines.append("```")

        if snapshot.dependency_summary:
            lines.extend(["", "## Dependencies", "```", snapshot.dependency_summary, "```"])

        if snapshot.memory_snapshot:
            lines.extend(["", "## User Preferences"])
            for key, value in snapshot.memory_snapshot.items():
                lines.append(f"- **{key}:** {value[:100]}")

        lines.append("")
        return "\n".join(lines)

    def flush_history(self, keep_lines: int = 50) -> None:
        """Truncate raw conversation history, keeping only essential context.

        Args:
            keep_lines: How many lines of history to retain.
        """
        log_path = self.root_path / ".hale" / "logs" / "conversation.log"
        if log_path.exists():
            try:
                lines = log_path.read_text().split("\n")
                if len(lines) > keep_lines:
                    log_path.write_text("\n".join(lines[-keep_lines:]))
                    logger.info("Bootstrap: Flushed conversation history to %d lines", keep_lines)
            except Exception:
                pass
