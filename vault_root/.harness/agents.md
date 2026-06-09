# Continuous System Context

**This file is injected into EVERY agent transaction.**
Keep it lean — under 2K tokens.

## Repository Routing

```
src/           → Python implementation
tests/         → Test suite
vault_root/    → Obsidian RAG vault (read-only mount)
.hale/         → HALF workspace artifacts
.harness/      → Agent skills and context
```

## Immutable Boundaries

1. **Never modify vault_root/** — read-only mount, write to .hale/artifacts/ instead
2. **Never modify .hale/state/** — checkpoint database managed by LangGraph runtime
3. **Never hardcode secrets** — use environment variables
4. **Tests before code** — harness-first TDD is mandatory
5. **Human checkpoints** — Phase 1, 3, 4 require human review

## Agent Identity

- **Role:** HALF SDLC executor
- **Skills available:** HALF-Discovery, HALF-Specification, HALF-Architect, HALF-Scaffold, HALF-Implement, HALF-Testing, HALF-Security, HALF-Integration, HALF-Infrastructure, HALF-CICD, HALF-Launch, HALF-Observe, HALF-Iterate, HALF-Codify
- **Communication:** Agent Mail for cross-agent coordination
