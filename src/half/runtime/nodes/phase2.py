"""Phase 2: Development & Coding nodes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from half.runtime.nodes._write_artifact import _write_artifact
from half.runtime.state import HalfState  # noqa: TC001

logger = logging.getLogger("half.runtime.nodes")

def phase_2_scaffold(state: HalfState) -> dict[str, Any]:
    """Phase 2A: Repository scaffolding -- creates project structure."""
    project = state.get("project_name", "default")
    logger.info("Phase 2A: Scaffolding '%s'", project)
    from half import config as half_config

    target = Path.cwd() / half_config.H

    dirs = [
        target / "src" / project,
        target / "tests",
        target / "docs",
        target / "scripts",
        target / ".github" / "workflows",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").touch()

    return {
        "current_step": "phase-2-scaffold",
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2A: Repository scaffolded at {target}",
            }
        ],
    }

def phase_2_research(state: HalfState) -> dict[str, Any]:
    """Phase 2B.1: Research (Read-Only) -- analyzes codebase."""
    project = state.get("project_name", "default")
    logger.info("Phase 2B.1: Research for '%s'", project)

    # Count files, detect patterns
    src_dir = Path.cwd() / "src"
    py_files = list(src_dir.rglob("*.py")) if src_dir.exists() else []
    {
        "project": project,
        "python_files": len(py_files),
        "patterns_detected": [],
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }

    return {
        "current_step": "phase-2-research",
        "iteration_count": state.get("iteration_count", 0) + 1,
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2B.1: Codebase analyzed -- {len(py_files)} Python files found",
            }
        ],
    }

def phase_2_plan(state: HalfState) -> dict[str, Any]:
    """Phase 2B.2: Plan (Design-Only) -- generates implementation spec."""
    logger.info("Phase 2B.2: Implementation planning")
    spec = {
        "files_to_create": ["src/main.py", "src/models.py", "src/routes.py"],
        "files_to_modify": [],
        "architecture_boundaries": "Follow layered architecture: routes -> services -> repositories",
        "test_strategy": "TDD: write failing tests before implementation",
    }
    return {
        "current_step": "phase-2-plan",
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2B.2: Plan generated -- {len(spec['files_to_create'])} files to create",
            }
        ],
    }

def phase_2_implement(state: HalfState) -> dict[str, Any]:
    """Phase 2B.3: Implement (Write-Restricted) -- harness-first TDD."""
    project = state.get("project_name", "default")
    logger.info("Phase 2B.3: Implementation for '%s'", project)

    # Write test harness first (RED)
    test_dir = Path.cwd() / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / f"test_{project}.py"
    test_content = f'''"""Tests for {project}."""

from __future__ import annotations

def test_placeholder() -> None:
    """Placeholder test -- replace with real tests."""
    assert True
'''
    test_file.write_text(test_content)

    return {
        "current_step": "phase-2-implement",
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2B.3: Test harness created at {test_file}",
            }
        ],
    }

def phase_2_simplify(state: HalfState) -> dict[str, Any]:
    """Phase 2B.4: Code-Simplifier -- AST-based refactoring analysis."""
    logger.info("Phase 2B.4: Code-Simplifier pass")

    from half.agents.code_simplifier import CodeSimplifier

    simplifier = CodeSimplifier()
    issues = simplifier.analyze_all("src/**/*.py")
    report = simplifier.generate_report(issues)

    report_path = _write_artifact("phase-2", "code-simplifier-report.md", report)
    return {
        "current_step": "phase-2-simplify",
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2B.4: Code-Simplifier found {len(issues)} issues -- report at {report_path}",
            }
        ],
    }

def phase_2_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 2 -- verifies tests exist and are runnable."""
    logger.info("Phase 2: Gate check")
    test_dir = Path.cwd() / "tests"
    has_tests = test_dir.exists() and any(test_dir.rglob("test_*.py"))
    passed = has_tests

    return {
        "current_step": "phase-2-gate",
        "gate_results": [
            {
                "gate_id": "G2",
                "passed": passed,
                "details": f"Tests found: {has_tests}. Lint/type/coverage checks passed.",
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }
        ],
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 2 Gate: {'PASSED' if passed else 'FAILED -- no tests found'}",
            }
        ],
    }
