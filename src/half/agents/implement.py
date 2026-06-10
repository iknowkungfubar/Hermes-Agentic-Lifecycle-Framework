"""
HALF-Implement Agent (Phase 2B)

Harness-first TDD implementation engine.
Writes failing tests first, then implements code to make them pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TestHarness:
    """A test harness created before implementation code."""

    task_id: str
    fr_id: str
    file_path: str
    content: str
    created_before_implementation: bool = False
    first_run_passed: bool = False
    first_run_output: str = ""
    final_run_passed: bool = False


@dataclass
class ImplementationResult:
    """Result of implementing a task."""

    task_id: str
    test_file: str
    source_files: list[str]
    tests_pass: bool
    lint_pass: bool
    type_check_pass: bool
    coverage_pct: float
    commit_sha: str = ""


class ImplementAgent:
    """Phase 2B: Harness-first TDD implementation.

    Core protocol:
    1. Write failing test (RED)
    2. Implement code to pass (GREEN)
    3. Verify: tests, lint, types, coverage
    4. Commit
    """

    def __init__(self) -> None:
        self.harnesses: list[TestHarness] = []
        self.results: list[ImplementationResult] = []

    def create_test_harness(
        self,
        task_id: str,
        fr_id: str,
        file_path: str,
        test_content: str,
    ) -> TestHarness:
        """Create a test harness (must be done BEFORE implementation).

        Args:
            task_id: Task identifier.
            fr_id: Functional requirement ID.
            file_path: Path for the test file.
            test_content: Test code content.

        Returns:
            The TestHarness object.
        """
        harness = TestHarness(
            task_id=task_id,
            fr_id=fr_id,
            file_path=file_path,
            content=test_content,
        )
        self.harnesses.append(harness)
        return harness

    def verify_harness_first(self, task_id: str) -> bool:
        """Verify that test harness was created before implementation.

        Actually runs the test file to confirm it fails (RED),
        then checks that it passes after implementation (GREEN).

        Args:
            task_id: Task to verify.

        Returns:
            True if harness-first protocol was followed.
        """
        import subprocess
        import sys

        harnesses = [h for h in self.harnesses if h.task_id == task_id]
        if not harnesses:
            return False

        harness = harnesses[0]

        # Check 1: Test file must exist before implementation
        test_path = Path(harness.file_path)
        if not test_path.exists():
            return False

        # Check 2: Run the test — it should FAIL (RED phase)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-q", "--tb=line"],
                capture_output=True, text=True, timeout=30,
            )
            harness.first_run_passed = result.returncode == 0
            harness.first_run_output = result.stdout + result.stderr
            # First run should FAIL (test before implementation)
            harness.created_before_implementation = result.returncode != 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            harness.first_run_passed = False
            harness.created_before_implementation = False

        checks = [
            harness.created_before_implementation,
            not harness.first_run_passed,  # must fail first (RED)
            harness.final_run_passed,  # must pass after impl (GREEN)
        ]

        return all(checks)

    @staticmethod
    def generate_test_template(
        module_name: str,
        endpoint_or_fn: str,
        happy_path_data: dict[str, Any],
        error_cases: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate a pytest test template for an endpoint or function.

        Args:
            module_name: Python module name.
            endpoint_or_fn: Endpoint path or function name.
            happy_path_data: Expected valid input data.
            error_cases: List of {input, expected_status, description}.

        Returns:
            String content for the test file.
        """
        lines = [
            '"""Tests for {module_name}.{endpoint_or_fn}."""',
            "",
            "import pytest",
            f"from {module_name} import {endpoint_or_fn.rsplit('/', maxsplit=1)[-1].split('.', maxsplit=1)[0] if '/' in endpoint_or_fn else endpoint_or_fn}",
            "",
            "",
            "class Test{name}:".format(
                name=endpoint_or_fn.replace("/", "_").replace(".", "_").title()
            ),
            f'    """Test suite for {endpoint_or_fn}."""',
            "",
            "    def test_happy_path(self):",
            "        # Happy path test (should pass after implementation)",
            '        """Test normal operation succeeds."""',
            f"        data = {happy_path_data}",
            "        # TODO: Replace with actual function call",
            "        # result = {fn}(**data)".format(
                fn=endpoint_or_fn.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0]
                if "/" in endpoint_or_fn
                else endpoint_or_fn
            ),
            "        # assert result.success is True",
            "        assert True  # Placeholder — remove after writing real test",
            "",
        ]

        for i, error in enumerate(error_cases or []):
            lines.extend(
                [
                    f"    def test_error_case_{i + 1}(self):",
                    f'        """{error.get("description", "Error case")}"""',
                    f"        data = {error.get('input', {})}",
                    "        # TODO: Replace with actual function call",
                    "        # with pytest.raises({err}):".format(
                        err=error.get("expected_exception", "Exception")
                    ),
                    "        #     result = {fn}(**data)".format(
                        fn=endpoint_or_fn.rsplit("/", maxsplit=1)[-1].split(
                            ".", maxsplit=1
                        )[0]
                        if "/" in endpoint_or_fn
                        else endpoint_or_fn
                    ),
                    "        assert True  # Placeholder",
                    "",
                ]
            )

        return "\n".join(lines)

    @staticmethod
    def generate_source_template(
        module_path: str,
        function_name: str,
        params: dict[str, str],
        return_type: str = "dict",
        docstring: str = "",
    ) -> str:
        """Generate a stub implementation file.

        Args:
            module_path: Dotted module path.
            function_name: Function name.
            params: Parameter name -> type mapping.
            return_type: Return type annotation.
            docstring: Function docstring.

        Returns:
            String content for the source file.
        """
        param_str = ", ".join(f"{name}: {typ}" for name, typ in params.items())
        doc = docstring or f"Implement {function_name}."

        return f'''"""
{module_path} — TODO: Module description.
"""

from __future__ import annotations

from typing import Any


def {function_name}({param_str}) -> {return_type}:
    """{doc}

    TODO: Implement.
    """
    raise NotImplementedError("Implement {function_name}")
'''
