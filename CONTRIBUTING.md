# Contributing to HALF

First off, thanks for taking the time to contribute! 🎉

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

1. Check the [issue tracker](https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework/issues) for existing reports
2. Use the bug report template when creating an issue
3. Include a minimal reproduction example

### Suggesting Features

1. Open a feature request issue
2. Describe the problem you're solving, not just the solution
3. Explain how it fits into the HALF framework's 5-phase model

### Pull Requests

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Make your changes**, following the coding conventions
4. **Write tests** for your changes (we use pytest)
5. **Run the full CI**: `make ready`
6. **Commit** using conventional commits: `feat:|fix:|refactor:|test:|docs:|chore:`
7. **Push** and open a PR

### Development Setup

```bash
# Clone
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework

# Install development dependencies
pip install uv
uv sync --group dev

# Install pre-commit hooks
pre-commit install

# Run tests
make test

# Run full CI
make ready
```

### Coding Conventions

- **Python 3.13+** — Use modern Python features (pattern matching, generics)
- **Type annotations** — All public functions must have full type annotations
- **TDD** — Write tests before implementation code
- **Docstrings** — Google-style docstrings for all public APIs
- **Commits** — Conventional commits: `feat:|fix:|refactor:|test:|docs:|chore:`
- **Line length** — 88 characters (ruff default)

### Project Structure

```
src/
├── half/            # Package root with version and CLI entrypoint
├── agents/          # 16 agent skill implementations
├── core/            # Orchestrator, gates, fail-safe, error budget
├── state/           # LangGraph state security module
├── runtime/         # LangGraph graph, checkpointer, nodes
├── agent_mail/      # Decentralized agent coordination
├── half_voice/      # Speech-to-text and text-to-speech
├── half_focalboard/ # Kanban API client
└── half_sidecar.py  # Tauri sidecar entrypoint
```

## Release Process

1. Version is managed in `VERSION` and `src/half/__init__.py`
2. Changes are documented in `CHANGELOG.md`
3. Releases are tagged with `v{version}` on master
4. Release builds produce: PyPI package + Tauri binaries

## Questions?

Open a [discussion](https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework/discussions) or issue.
