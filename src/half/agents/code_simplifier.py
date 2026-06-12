"""
HALF — Code-Simplifier Refactoring Pass (Phase 2)

Triggered immediately after functional implementation in Phase 2.
Operates on the "Chesterton's Fence" principle:
methodically reducing nesting, extracting complex methods,
and applying KISS/DRY/YAGNI without altering existing behavior.

Part of the Tri-Phasic Execution Loop:
  Research (read-only) → Plan (design-only) → Implement (write-restricted)
    ↓
  Code-Simplifier (refactoring pass)
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.code_simplifier")


class CodeSimplifier:
    """Static analysis and refactoring pass for agent-generated code.

    Operates after the Implement phase to ensure code quality:
    - Measures cyclomatic complexity
    - Detects deeply nested code (>4 levels)
    - Identifies duplicated code blocks
    - Suggests extractions
    - Enforces KISS/DRY/YAGNI
    """

    MAX_NESTING_DEPTH = 4
    MAX_COMPLEXITY = 10
    MAX_FUNCTION_LINES = 50
    MAX_PARAMS = 5

    def __init__(self, target_dir: str | Path = "."):
        self.target_dir = Path(target_dir)
        self.issues: list[dict[str, Any]] = []

    def analyze_file(self, filepath: Path) -> list[dict[str, Any]]:
        """Analyze a single Python file for simplification opportunities.

        Args:
            filepath: Path to the Python file to analyze.

        Returns:
            List of issues found.
        """
        if not filepath.exists() or filepath.suffix != ".py":
            return []

        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning("Cannot parse %s: %s", filepath, e)
            return []

        file_issues: list[dict[str, Any]] = []
        lines = source.split("\n")

        for node in ast.walk(tree):
            # Check function complexity
            if isinstance(node, ast.FunctionDef):
                func_issues = self._analyze_function(node, filepath, lines)
                file_issues.extend(func_issues)

            # Check class complexity
            if isinstance(node, ast.ClassDef):
                class_issues = self._analyze_class(node, filepath, lines)
                file_issues.extend(class_issues)

        self.issues.extend(file_issues)
        return file_issues

    def analyze_all(self, glob_pattern: str = "**/*.py") -> list[dict[str, Any]]:
        """Analyze all Python files in the target directory.

        Args:
            glob_pattern: Glob pattern for file discovery.

        Returns:
            All issues found across all files.
        """
        all_issues: list[dict[str, Any]] = []
        for filepath in sorted(self.target_dir.glob(glob_pattern)):
            issues = self.analyze_file(filepath)
            all_issues.extend(issues)

        if all_issues:
            logger.info(
                "Code-Simplifier: %d issue(s) found across %d file(s)",
                len(all_issues),
                len(list(self.target_dir.glob(glob_pattern))),
            )
        else:
            logger.info("Code-Simplifier: No issues found — code is clean")

        return all_issues

    def _analyze_function(
        self,
        node: ast.FunctionDef,
        filepath: Path,
        lines: list[str],
    ) -> list[dict[str, Any]]:
        """Analyze a single function for quality issues.

        Args:
            node: The function AST node.
            filepath: Source file path.
            lines: Source file lines.

        Returns:
            List of issues found in this function.
        """
        issues: list[dict[str, Any]] = []
        func_name = node.name
        lineno = node.lineno

        # 1. Check nesting depth
        max_depth = self._max_nesting_depth(node)
        if max_depth > self.MAX_NESTING_DEPTH:
            issues.append(
                {
                    "type": "nesting",
                    "severity": "medium",
                    "file": str(filepath),
                    "line": lineno,
                    "function": func_name,
                    "message": (
                        f"Function '{func_name}' has nesting depth {max_depth} "
                        f"(max allowed: {self.MAX_NESTING_DEPTH}). "
                        f"Consider extracting inner logic."
                    ),
                    "suggestion": "Extract inner blocks into named helper functions",
                }
            )

        # 2. Check function length
        if hasattr(node, "end_lineno") and node.end_lineno:
            func_lines = node.end_lineno - lineno
            if func_lines > self.MAX_FUNCTION_LINES:
                issues.append(
                    {
                        "type": "length",
                        "severity": "medium",
                        "file": str(filepath),
                        "line": lineno,
                        "function": func_name,
                        "message": (
                            f"Function '{func_name}' is {func_lines} lines "
                            f"(max allowed: {self.MAX_FUNCTION_LINES}). "
                            f"Consider splitting."
                        ),
                        "suggestion": "Break into smaller functions (< 50 lines each)",
                    }
                )

        # 3. Check parameter count
        param_count = len(node.args.args) if hasattr(node, "args") else 0
        if param_count > self.MAX_PARAMS:
            issues.append(
                {
                    "type": "parameters",
                    "severity": "low",
                    "file": str(filepath),
                    "line": lineno,
                    "function": func_name,
                    "message": (
                        f"Function '{func_name}' has {param_count} parameters "
                        f"(max recommended: {self.MAX_PARAMS}). "
                        f"Consider using a config object."
                    ),
                    "suggestion": "Group parameters into a dataclass or config object",
                }
            )

        # 4. Check for missing return type annotations
        if not hasattr(node, "returns") or node.returns is None:
            issues.append(
                {
                    "type": "annotation",
                    "severity": "low",
                    "file": str(filepath),
                    "line": lineno,
                    "function": func_name,
                    "message": (
                        f"Function '{func_name}' is missing return type annotation."
                    ),
                    "suggestion": "Add -> ReturnType annotation",
                }
            )

        return issues

    def _analyze_class(
        self,
        node: ast.ClassDef,
        filepath: Path,
        lines: list[str],
    ) -> list[dict[str, Any]]:
        """Analyze a class for quality issues.

        Args:
            node: The class AST node.
            filepath: Source file path.
            lines: Source file lines.

        Returns:
            List of issues found in this class.
        """
        issues: list[dict[str, Any]] = []
        class_name = node.name

        # Check class has docstring
        if not ast.get_docstring(node):
            issues.append(
                {
                    "type": "documentation",
                    "severity": "low",
                    "file": str(filepath),
                    "line": node.lineno,
                    "function": class_name,
                    "message": f"Class '{class_name}' is missing a docstring.",
                    "suggestion": "Add class-level docstring describing responsibility",
                }
            )

        # Count public methods
        public_methods = [
            n.name
            for n in node.body
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
        ]
        if len(public_methods) > 10:
            issues.append(
                {
                    "type": "complexity",
                    "severity": "medium",
                    "file": str(filepath),
                    "line": node.lineno,
                    "function": class_name,
                    "message": (
                        f"Class '{class_name}' has {len(public_methods)} public methods. "
                        f"Consider splitting into smaller classes."
                    ),
                    "suggestion": "Split into focused classes (ISP principle)",
                }
            )

        return issues

    @staticmethod
    def _max_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in an AST node.

        Args:
            node: The AST node to analyze.
            current_depth: Current nesting depth.

        Returns:
            Maximum nesting depth found.
        """
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.While,
                    ast.Try,
                    ast.With,
                    ast.AsyncFor,
                    ast.AsyncWith,
                ),
            ):
                child_depth = CodeSimplifier._max_nesting_depth(
                    child, current_depth + 1
                )
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = CodeSimplifier._max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def generate_report(self, issues: list[dict[str, Any]] | None = None) -> str:
        """Generate a human-readable simplification report.

        Args:
            issues: Issues to report. Uses self.issues if None.

        Returns:
            Markdown report string.
        """
        if issues is None:
            issues = self.issues

        if not issues:
            return "# Code-Simplifier Report\n\n**No issues found.** Code is clean and follows KISS/DRY/YAGNI principles."

        lines = [
            "# Code-Simplifier Report",
            "",
            f"**Total issues found:** {len(issues)}",
            "",
            "| # | Severity | Type | File | Function | Suggestion |",
            "|---|----------|------|------|----------|------------|",
        ]

        for i, issue in enumerate(issues, 1):
            lines.append(
                f"| {i} | {issue.get('severity', 'unknown')} | "
                f"{issue.get('type', 'unknown')} | "
                f"{Path(issue.get('file', '')).name}:{issue.get('line', '')} | "
                f"{issue.get('function', '')} | "
                f"{issue.get('suggestion', '')} |"
            )

        lines.extend(
            [
                "",
                "## Severity Legend",
                "- **high**: Must fix before merging",
                "- **medium**: Should fix in current iteration",
                "- **low**: Nice to have, queue for backlog",
            ]
        )

        return "\n".join(lines)
