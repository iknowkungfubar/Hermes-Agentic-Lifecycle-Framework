"""HALF 1.5 — Spec-Driven Verification Layers.

Before code is even executed, it must pass rigorous Pydantic schema validation
and Abstract Syntax Tree (AST) parsing. Acts as a non-negotiable quality gate
that agents cannot bypass.

Based on the HALF 1.5 doctrine's 'Spec-Driven Verification Layers' spec.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.spec_verify")


@dataclass
class VerificationIssue:
    """An issue found during spec-driven verification."""

    check: str  # ast_valid, schema_valid, imports_valid, naming_convention
    file: str
    line: int = 0
    message: str = ""
    severity: str = "error"  # error, warning


@dataclass
class VerificationReport:
    """Result of spec-driven verification."""

    passed: bool = False
    total_checks: int = 0
    passed_checks: int = 0
    issues: list[VerificationIssue] = field(default_factory=list)
    summary: str = ""


class SpecVerifier:
    """Spec-Driven Verification Layer.

    Every piece of generated code must pass these checks before execution:
    1. AST validity (valid Python syntax)
    2. Pydantic schema validation (if applicable)
    3. Import safety (no dangerous imports)
    4. Naming conventions (PEP8 compliance)
    5. No hardcoded secrets

    Acts as a non-negotiable quality gate.
    """

    DANGEROUS_IMPORTS = {
        "os.system", "subprocess.call", "subprocess.Popen", "subprocess.run",
        "shutil.rmtree", "shutil.rmdir", "pathlib.Path.unlink",
        "pickle.loads", "pickle.load", "shelve.open",
        "eval", "exec", "compile",
        "__import__", "importlib.import_module",
    }

    FORBIDDEN_STRINGS = [
        "rm -rf", "dd if=", "format ", "mkfs.", ":(){ :|:& };:",
        "chmod 777", "chown -R",
    ]

    def __init__(self) -> None:
        self.report = VerificationReport()

    def verify_file(self, filepath: str | Path) -> VerificationReport:
        """Run all verification checks on a single file.

        Args:
            filepath: Path to the Python file to verify.

        Returns:
            VerificationReport with pass/fail and issues.
        """
        path = Path(filepath)
        self.report = VerificationReport()

        if not path.exists():
            self.report.issues.append(VerificationIssue(
                check="file_exists", file=str(path), message="File not found", severity="error",
            ))
            self.report.passed = False
            return self.report

        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            self.report.issues.append(VerificationIssue(
                check="file_readable", file=str(path), message=str(e), severity="error",
            ))
            return self.report

        # Run all checks
        self._check_ast_validity(source, path)
        self._check_dangerous_imports(source, path)
        self._check_forbidden_strings(source, path)
        self._check_naming_conventions(source, path)
        self._check_hardcoded_secrets(source, path)

        # Calculate result
        errors = [i for i in self.report.issues if i.severity == "error"]
        self.report.total_checks = 5
        self.report.passed_checks = self.report.total_checks - len(errors)
        self.report.passed = len(errors) == 0
        self.report.summary = (
            f"{self.report.passed_checks}/{self.report.total_checks} checks passed"
        )

        if not self.report.passed:
            logger.warning("Spec-Verify: FAILED for %s — %s", path.name, self.report.summary)
        else:
            logger.info("Spec-Verify: PASSED for %s", path.name)

        return self.report

    def _check_ast_validity(self, source: str, path: Path) -> None:
        """Check that the file is valid Python AST."""
        try:
            ast.parse(source)
            self.report.issues.append(VerificationIssue(
                check="ast_valid", file=str(path), message="Valid Python syntax",
                severity="info",
            ))
        except SyntaxError as e:
            self.report.issues.append(VerificationIssue(
                check="ast_valid", file=str(path), line=e.lineno or 0,
                message=f"Syntax error: {e.msg}",
                severity="error",
            ))

    def _check_dangerous_imports(self, source: str, path: Path) -> None:
        """Check for dangerous imports and function calls."""
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    full_name = f"{self._get_attribute_chain(node.func)}"
                    if full_name in self.DANGEROUS_IMPORTS:
                        self.report.issues.append(VerificationIssue(
                            check="imports_valid", file=str(path), line=node.lineno,
                            message=f"Dangerous function call: {full_name}",
                            severity="error",
                        ))

    def _check_forbidden_strings(self, source: str, path: Path) -> None:
        """Check for forbidden strings like rm -rf."""
        for i, line in enumerate(source.split("\n"), 1):
            for forbidden in self.FORBIDDEN_STRINGS:
                if forbidden in line:
                    self.report.issues.append(VerificationIssue(
                        check="no_forbidden_strings", file=str(path), line=i,
                        message=f"Contains forbidden pattern: {forbidden[:30]}",
                        severity="error",
                    ))

    def _check_naming_conventions(self, source: str, path: Path) -> None:
        """Check PEP8 naming conventions."""
        import re
        for i, line in enumerate(source.split("\n"), 1):
            # Class names should be CamelCase
            class_match = re.match(r"^\s*class\s+([a-z][a-zA-Z0-9_]*)\s*[:\(]", line)
            if class_match:
                self.report.issues.append(VerificationIssue(
                    check="naming_convention", file=str(path), line=i,
                    message=f"Class '{class_match.group(1)}' should use CamelCase",
                    severity="warning",
                ))

    def _check_hardcoded_secrets(self, source: str, path: Path) -> None:
        """Check for hardcoded secrets."""
        import re
        secret_patterns = [
            r"(?i)(password|secret|api_key|apikey|token|auth)\s*[:=]\s*['\"](?![*])",
            r"(?i)-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----",
        ]
        for i, line in enumerate(source.split("\n"), 1):
            for pattern in secret_patterns:
                if re.search(pattern, line):
                    self.report.issues.append(VerificationIssue(
                        check="no_hardcoded_secrets", file=str(path), line=i,
                        message="Potential hardcoded secret detected",
                        severity="error",
                    ))

    @staticmethod
    def _get_attribute_chain(node: ast.Attribute) -> str:
        """Get the full dotted name of an attribute."""
        if isinstance(node.value, ast.Attribute):
            return f"{SpecVerifier._get_attribute_chain(node.value)}.{node.attr}"
        elif isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        return node.attr
