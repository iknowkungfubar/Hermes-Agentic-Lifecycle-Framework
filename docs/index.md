# Welcome to HALF

**HALF (Hermes Agentic Lifecycle Framework)** is a modular, template-driven
framework that enables AI agents to autonomously execute the full software
development lifecycle — from a high-level business concept to a production-ready
software product.

## Why HALF?

Traditional software development requires humans to write every line of code,
review every PR, and manage every deployment. HALF changes this by providing
a **structured, gated framework** where AI agents handle execution while
humans focus on high-level decisions.

### The Five Phases

```
CONCEPT
   ↓
Phase 1: Discovery & Strategy  →  Technical Spec + Architecture
   ↓  ← Human Checkpoint
Phase 2: Development & Coding  →  Modular, tested codebase
   ↓
Phase 3: Quality Assurance     →  Tests + Security + Red-Teaming
   ↓  ← Human Checkpoint
Phase 4: Polish & Deployment   →  IaC + CI/CD + Launch State
   ↓  ← Human Checkpoint (Finality Gate)
Phase 5: Iteration             →  Feedback Loops + QoL Updates
   ↓
PRODUCTION SOFTWARE PRODUCT
```

### Key Concepts

- **Agent Execution Environment (AEE)** — Multi-agent swarms performing tasks
- **Agent Command Environment (ACE)** — Human orchestrators mentor agent teams
- **Tri-Phasic Execution Loop** — Research (read-only) → Plan (design-only) → Implement (write-restricted)
- **Gate Checks** — Every phase has quality gates that must pass before proceeding
- **Fail-Safe Protocol** — 3-level escalation: step retry → phase retry → human gap report
- **Codification Imperative** — Every manual fix becomes a durable improvement

## Quick Install

```bash
pip install uv
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework
uv sync --group dev
half version
```

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Your First Project](getting-started/first-project.md)
