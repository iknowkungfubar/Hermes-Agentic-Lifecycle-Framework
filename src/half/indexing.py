"""HALF — Repository Indexing Module.

Hierarchical summarization and indexing for codebase navigation.
Prevents context rot by building a summary tree that agents navigate
before reading raw files.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.indexing")


class RepoIndexer:
    """Builds a hierarchical summary tree of a codebase.

    Agents navigate this tree to find relevant files before reading
    raw code, protecting the context window.
    """

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self._index: dict[str, Any] = {}
        self._built = False

    def build_index(self, max_depth: int = 4) -> dict[str, Any]:
        """Build the hierarchical index of the codebase.

        Args:
            max_depth: Maximum directory depth to index.

        Returns:
            Nested dict representing the codebase structure.
        """
        self._index = self._index_directory(self.root, max_depth, 0)
        self._built = True
        logger.info("Index built for %s", self.root)
        return self._index

    def _index_directory(
        self, directory: Path, max_depth: int, current_depth: int
    ) -> dict[str, Any]:
        """Recursively index a directory."""
        if current_depth > max_depth:
            return {"__type__": "depth_limit", "__files__": len(list(directory.iterdir())) if directory.exists() else 0}

        result: dict[str, Any] = {"__type__": "directory", "__files__": [], "__dirs__": {}}
        if not directory.exists():
            return result

        for item in sorted(directory.iterdir()):
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            if item.is_file() and item.suffix == ".py":
                summary = self._summarize_file(item)
                result["__files__"].append(summary)
            elif item.is_dir():
                sub = self._index_directory(item, max_depth, current_depth + 1)
                result["__dirs__"][item.name] = sub

        return result

    def _summarize_file(self, filepath: Path) -> dict[str, Any]:
        """Create a semantic summary of a Python file."""
        try:
            source = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return {"name": filepath.name, "type": "error", "summary": "Cannot read file"}

        tree = ast.parse(source)
        classes = []
        functions = []
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({"name": node.name, "methods": methods})
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                else:
                    module = node.module or ""
                    imports.extend(f"{module}.{alias.name}" if module else alias.name for alias in node.names)

        return {
            "name": filepath.name,
            "path": str(filepath.relative_to(self.root)) if filepath != self.root else filepath.name,
            "type": "python",
            "lines": len(source.split("\n")),
            "classes": classes,
            "functions": functions[:10],  # Top 10 to save context
            "imports": imports[:10],
            "docstring": ast.get_docstring(tree) or "",
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search the index for files matching a query.

        Args:
            query: Search term.

        Returns:
            List of matching file summaries.
        """
        if not self._built:
            self.build_index()

        results = []
        query_lower = query.lower()

        def _search(node: dict[str, Any], path: str = "") -> None:
            for f in node.get("__files__", []):
                if query_lower in f.get("name", "").lower() or query_lower in f.get("docstring", "").lower():
                    results.append(f)
                for func in f.get("functions", []):
                    if query_lower in func.lower():
                        results.append(f)
                        break
            for name, sub in node.get("__dirs__", {}).items():
                _search(sub, f"{path}/{name}")

        _search(self._index)
        return results

    def get_summary(self) -> dict[str, Any]:
        """Get a human-readable summary of the codebase."""
        if not self._built:
            self.build_index()

        total_files = 0
        total_classes = 0
        total_functions = 0

        def _count(node: dict[str, Any]) -> None:
            nonlocal total_files, total_classes, total_functions
            total_files += len(node.get("__files__", []))
            for f in node.get("__files__", []):
                total_classes += len(f.get("classes", []))
                total_functions += len(f.get("functions", []))
            for sub in node.get("__dirs__", {}).values():
                _count(sub)

        _count(self._index)

        return {
            "root": str(self.root),
            "total_files": total_files,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "depth": self._get_depth(self._index),
        }

    @staticmethod
    def _get_depth(node: dict[str, Any], current: int = 0) -> int:
        max_d = current
        for sub in node.get("__dirs__", {}).values():
            max_d = max(max_d, RepoIndexer._get_depth(sub, current + 1))
        return max_d
