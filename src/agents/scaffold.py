"""
HALF-Scaffold Agent (Phase 2A)

Creates the repository structure, configures tooling, and sets up CI/CD.
"""

from __future__ import annotations

from pathlib import Path


class ScaffoldAgent:
    """Phase 2A: Repository scaffolding and tooling configuration."""

    PYPROJECT_TOML_TEMPLATE = """\
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "{description}"
requires-python = ">=3.13"

[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = ["ALL"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
show_missing = true
"""

    AGENTS_MD_TEMPLATE = """\
# {project_name} — Project Context for AI Agents

## Tech Stack
- Language: {language}
- Testing: {test_runner}
- Linting: {lint_tool}
- Formatting: {formatter}
- Type Checking: {type_checker}

## Conventions
- TDD: Write tests BEFORE implementation
- Commit messages: `feat:|fix:|refactor:|test:|docs: [scope] — [message]`
- All public functions have type annotations and docstrings
- {extra_conventions}

## Architecture
See .hale/artifacts/phase-1/04-ARCHITECTURE.md
API contracts: 02-SPECIFICATION.md

## Quality Gates (pre-commit)
- {lint_tool} — 0 errors
- {type_checker} — 0 errors
- {test_runner} — all tests pass
- Coverage > 80%
"""

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def scaffold_project(
        self,
        project_name: str,
        description: str = "",
        language: str = "python",
    ) -> dict[str, str]:
        """Create the repository structure.

        Args:
            project_name: The project/module name.
            description: Short project description.
            language: Programming language (python, rust, typescript).

        Returns:
            Dict mapping file paths to contents.
        """
        created: dict[str, str] = {}

        # Create directories
        dirs = [
            self.target_dir / "src" / project_name,
            self.target_dir / "tests",
            self.target_dir / "docs",
            self.target_dir / "scripts",
            self.target_dir / ".github" / "workflows",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # Write files
        created[str(self.target_dir / "README.md")] = self._readme(
            project_name, description
        )
        created[str(self.target_dir / ".gitignore")] = self._gitignore(project_name)
        created[str(self.target_dir / ".editorconfig")] = self._editorconfig()

        if language == "python":
            created[str(self.target_dir / "pyproject.toml")] = (
                self.PYPROJECT_TOML_TEMPLATE.format(
                    project_name=project_name,
                    description=description or "A HALF-generated project",
                )
            )
            created[str(self.target_dir / "src" / project_name / "__init__.py")] = ""
            created[str(self.target_dir / "tests" / "__init__.py")] = ""

        # AGENTS.md
        created[str(self.target_dir / "AGENTS.md")] = self._agents_md(
            project_name, language
        )

        # CI workflow
        created[str(self.target_dir / ".github" / "workflows" / "ci.yml")] = (
            self._ci_workflow(language)
        )

        return created

    def _readme(self, project_name: str, description: str) -> str:
        return f"""\
# {project_name}

{description}

## Getting Started

```bash
# Clone and enter
git clone <repo-url>
cd {project_name}

# Install dependencies
# (language-specific instructions)
```

## Development

This project was scaffolded by [HALF](https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework).

## Quality Gates

- Lint: 0 errors
- Type check: 0 errors
- Tests: all pass
- Coverage: ≥80%
"""

    def _gitignore(self, project_name: str) -> str:
        return """\
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
.venv/
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Project
.env
*.log
.hale/

# Docker
.docker/
"""

    def _editorconfig(self) -> str:
        return """\
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{yml,yaml,json}]
indent_size = 2
"""

    def _agents_md(self, project_name: str, language: str) -> str:
        configs: dict[str, dict[str, str]] = {
            "python": {
                "test_runner": "pytest",
                "lint_tool": "ruff",
                "formatter": "ruff format",
                "type_checker": "mypy",
                "extra": "FastAPI-style route handlers with Pydantic schemas",
            },
            "rust": {
                "test_runner": "cargo test",
                "lint_tool": "clippy",
                "formatter": "rustfmt",
                "type_checker": "rustc",
                "extra": "Error handling with anyhow/thiserror",
            },
            "typescript": {
                "test_runner": "vitest",
                "lint_tool": "eslint",
                "formatter": "prettier",
                "type_checker": "tsc --strict",
                "extra": "ESM modules, Next.js App Router conventions",
            },
        }
        cfg = configs.get(language, configs["python"])

        return self.AGENTS_MD_TEMPLATE.format(
            project_name=project_name,
            language=language.capitalize(),
            test_runner=cfg["test_runner"],
            lint_tool=cfg["lint_tool"],
            formatter=cfg["formatter"],
            type_checker=cfg["type_checker"],
            extra_conventions=cfg["extra"],
        )

    def _ci_workflow(self, language: str) -> str:
        if language == "python":
            return """\
name: CI

on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install uv && uv sync
      - run: ruff check src/ tests/
      - run: mypy src/
      - run: pytest --cov=src/ --cov-fail-under=80
"""
        return """\
name: CI

on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "CI pipeline to be configured for your language"
"""
