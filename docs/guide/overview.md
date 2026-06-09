# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Agent Command Environment (ACE)          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Focalboard   │  │ Agent Mail   │  │ Tauri GUI      │  │
│  │ (Kanban)     │  │ (Messages)   │  │ (Finality Gate)│  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘  │
│         │               │                  │            │
└─────────┼───────────────┼──────────────────┼────────────┘
          │               │                  │
          ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Execution Environment (AEE)            │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │           LangGraph State Machine                 │   │
│  │  Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 │   │
│  │           ↕ (iteration cycle)                     │   │
│  └──────────────────────────────────────────────────┘   │
│          │              │              │                │
│          ▼              ▼              ▼                │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐    │
│  │ 16 Agent │  │ Code-        │  │ Gate Checks    │    │
│  │  Skills  │  │ Simplifier   │  │ G1-G5          │    │
│  └──────────┘  └──────────────┘  └────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
          │              │              │
          ▼              ▼              ▼
┌──────────┐  ┌──────────────┐  ┌────────────────┐
│ Obsidian  │  │ FOSS Stack   │  │ CI/CD Pipeline │
│ Vault     │  │ (LangWatch,  │  │ (GitHub Actions│
│ (RAG)     │  │  Laminar,    │  │  → Deploy)     │
└──────────┘  │  Prometheus)  │  └────────────────┘
              └──────────────┘
```

## Core Components

### Phase Orchestrator
Manages the 5-phase lifecycle, injects context, dispatches agents, invokes gates.

### State Machine (LangGraph)
Persistent, stateful graph with SQLite/WAL checkpoints. Each node is a phase step.
Human interrupts at Phase 1, 3, and 4 gates.

### Agent Skills
16 specialized agents: Discovery, Specification, Architect, Scaffold, Research,
Plan, Implement, Simplify, Testing, Security, Integration, Infrastructure,
CICD, Launch, Observe, Iterate, Codify.

### Fail-Safe Protocol
3 levels: step retry (×3) → phase retry (×2) → human gap report.
Circuit breakers for test cascades, security criticals, deployment failures.

### Error Budget
100 points/30 days. Deductions per failure type. Warning at <40%, critical at <20%,
exhausted at 0%.
