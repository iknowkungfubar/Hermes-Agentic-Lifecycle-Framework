# HALF — Hermes Agentic Lifecycle Framework

## Project Context for AI Agents

### Tech Stack
- **Language:** Python 3.13+
- **Package Manager:** uv (pip as fallback)
- **Linting:** ruff (select = ["ALL"], ignore = ["D", "ANN"])
- **Formatting:** ruff format
- **Type Checking:** mypy --strict
- **Testing:** pytest with pytest-asyncio
- **Documentation:** Markdown with Mermaid diagrams

### What HALF Is
HALF is a modular, template-driven framework that transforms high-level business concepts into production-ready software. It implements the 5-phase SDLC from the Hermes Agentic Lifecycle Framework doctrine:

1. **Discovery & Strategy** — Requirements → Spec → Architecture → Tasks
2. **Development & Coding** — TDD, harness-first, parallel dependency dispatch
3. **Quality Assurance** — Test completeness, security audit, adversarial red-teaming
4. **Polish & Deployment** — IaC, CI/CD, production readiness checklist
5. **Iteration** — Monitoring, triage, codification, QoL updates

### Repository Structure
```
├── SKILL.md                    # Core framework (the "doctrine")
├── AGENTS.md                   # This file — agent context
├── README.md                   # Project documentation
├── src/                        # Python implementation
│   ├── state/                  # LangGraph state machine
│   ├── core/                   # Orchestrator, gates, fail-safes
│   └── agents/                 # 16 agent skill implementations
├── references/                 # Quick-start guides
├── templates/                  # YAML/MD templates
├── config/                     # Example configurations
├── examples/                   # Sample output walkthroughs
├── scripts/                    # Shell bootstrap/utility scripts
├── docker/                     # Docker build + compose files
└── .github/workflows/          # CI/CD pipeline templates
```

### Conventions
- **Commits:** `feat:|fix:|refactor:|test:|docs:|chore: [scope] — [message]`
- **Tests before code** — TDD is mandatory in Phase 2
- **All public functions** have type annotations and docstrings
- **Config validation** via pydantic-settings
- **Artifacts** live at `.hale/artifacts/phase-N/` during execution

### Quality Gates (this repo)
- ruff check — 0 errors
- ruff format — check passes
- mypy — strict mode, 0 errors
- pytest — all tests pass
