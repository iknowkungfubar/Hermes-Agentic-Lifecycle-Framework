"""HALF — No-Slop Subagent Context Architecture.

Hierarchical RAG indexing using semantic token parsing and directory-level
summaries. Agents must navigate the summary tree before reading explicit code,
preventing context window pollution.

Based on the HALF doctrine's 'No-Slop Architecture' specification.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.no_slop")


@dataclass
class SemanticToken:
    """A parsed semantic token from source code."""

    type: str  # function, class, import, variable, comment
    name: str
    line: int
    docstring: str = ""
    complexity: int = 0


@dataclass
class DirectorySummary:
    """Aggregated summary of a directory's contents."""

    path: str
    file_count: int = 0
    total_lines: int = 0
    tokens: list[SemanticToken] = field(default_factory=list)
    child_dirs: list[str] = field(default_factory=list)
    summary: str = ""


class NoSlopIndexer:
    """Hierarchical RAG indexing engine.

    Parses source files into semantic tokens, aggregates into directory-level
    summaries, and builds a navigable tree. Agents use the tree to find
    relevant files before reading full content.
    """

    def __init__(self, root_path: str | Path = "."):
        self.root_path = Path(root_path).resolve()
        self._summaries: dict[str, DirectorySummary] = {}

    def build_index(self) -> dict[str, DirectorySummary]:
        """Build the hierarchical index from the root path.

        Returns:
            Dict of directory path -> DirectorySummary.
        """
        logger.info("No-Slop: Building index from %s", self.root_path)
        self._summaries = {}

        for dirpath in sorted(self.root_path.rglob("*")):
            if dirpath.is_dir() and not any(
                p.startswith(".") for p in dirpath.relative_to(self.root_path).parts
            ):
                summary = self._summarize_directory(dirpath)
                self._summaries[str(dirpath.relative_to(self.root_path))] = summary

        logger.info("No-Slop: Indexed %d directories", len(self._summaries))
        return self._summaries

    def _summarize_directory(self, dirpath: Path) -> DirectorySummary:
        """Create a summary of a directory's contents."""
        rel = dirpath.relative_to(self.root_path)
        summary = DirectorySummary(path=str(rel))
        tokens: list[SemanticToken] = []

        for py_file in sorted(dirpath.glob("*.py")):
            file_tokens = self._parse_file(py_file)
            tokens.extend(file_tokens)
            summary.file_count += 1
            try:
                summary.total_lines += len(py_file.read_text().split("\n"))
            except Exception:
                pass

        # Generate human-readable summary
        funcs = [t for t in tokens if t.type == "function"]
        classes = [t for t in tokens if t.type == "class"]
        imports = [t for t in tokens if t.type == "import"]

        desc_parts = []
        if classes:
            desc_parts.append(f"{len(classes)} classes")
        if funcs:
            desc_parts.append(f"{len(funcs)} functions")
        desc_parts.append(f"{summary.file_count} files, {summary.total_lines} lines")
        if imports:
            desc_parts.append(f"{len(imports)} imports")

        summary.tokens = tokens[:20]  # Keep top 20 tokens for context
        summary.summary = ", ".join(desc_parts)

        return summary

    def _parse_file(self, filepath: Path) -> list[SemanticToken]:
        """Parse a Python file into semantic tokens."""
        tokens: list[SemanticToken] = []
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return tokens

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node) or ""
                tokens.append(SemanticToken(
                    type="function",
                    name=node.name,
                    line=node.lineno,
                    docstring=doc[:100],
                    complexity=self._compute_complexity(node),
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                tokens.append(SemanticToken(
                    type="class",
                    name=node.name,
                    line=node.lineno,
                    docstring=f"{doc[:80]} ({len(methods)} methods)",
                ))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    tokens.append(SemanticToken(
                        type="import",
                        name=alias.name,
                        line=node.lineno,
                    ))

        return tokens

    @staticmethod
    def _compute_complexity(node: ast.FunctionDef) -> int:
        """Compute cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.AsyncFor, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def find_relevant_files(self, query: str, max_results: int = 5) -> list[str]:
        """Find files relevant to a query by matching tokens.

        Args:
            query: Search query.
            max_results: Max files to return.

        Returns:
            List of relevant file paths relative to root.
        """
        keywords = re.findall(r"\w+", query.lower())
        scored: dict[str, float] = {}

        for rel_path, summary in self._summaries.items():
            score = 0.0
            for token in summary.tokens:
                for kw in keywords:
                    if kw in token.name.lower() or kw in token.docstring.lower():
                        score += 1.0
                    if kw in summary.summary.lower():
                        score += 0.5
            if score > 0:
                scored[rel_path] = score

        sorted_results = sorted(scored.items(), key=lambda x: -x[1])
        return [path for path, _ in sorted_results[:max_results]]

    def print_tree(self, max_depth: int = 3) -> str:
        """Print the hierarchical index tree.

        Args:
            max_depth: Maximum depth to print.

        Returns:
            ASCII tree representation.
        """
        lines: list[str] = ["# No-Slop Index Tree", ""]

        def _print_dir(rel: str, depth: int) -> None:
            if depth > max_depth:
                return
            summary = self._summaries.get(rel)
            if not summary:
                return
            indent = "  " * depth
            lines.append(f"{indent}{rel}/ ({summary.summary})")
            for child in sorted(summary.child_dirs):
                _print_dir(child, depth + 1)

        _print_dir(".", 0)
        return "\n".join(lines)
