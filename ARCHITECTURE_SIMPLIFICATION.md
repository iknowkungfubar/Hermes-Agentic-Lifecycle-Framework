# HALF Architecture Simplification Plan

> **Status**: Proposal  
> **Date**: 2026-06-18  
> **Replaces**: Current monolithic architecture with 10,388 lines across 100+ files, 5 CI workflows, and 5 external service dependencies

## Problem Statement

HALF has grown to 10,388 lines of Python across 100+ files with 5 external service dependencies (Prometheus, Grafana, Focalboard, PostgreSQL, Agent Mail DB) plus a Tauri 2.0 GUI. This complexity:

- **Blocks adoption**: Users need Docker + multiple services just to try it
- **Slows development**: Every change touches multiple layers
- **Increases CI cost**: 5 workflows to maintain
- **Hides value**: The core 5-phase SDLC engine is buried under infrastructure

## Recommended Split

```
┌─────────────────────────────────────────────────────┐
│                  hermes-half-core                     │
│  CLI + 5-phase engine + LangGraph + 16 agents        │
│  Dependencies: pydantic, pyyaml, langgraph           │
│  Install: pip install hermes-half                    │
├─────────────────────────────────────────────────────┤
│                  hermes-half-gui                      │
│  Tauri 2.0 desktop app (optional)                    │
│  Requires: half-core running                          │
│  Install: Download from GitHub releases               │
├─────────────────────────────────────────────────────┤
│                  hermes-half-infra                    │
│  Docker Compose with optional services                │
│  Prometheus, Grafana, Focalboard, PostgreSQL           │
│  Run: docker compose up                               │
└─────────────────────────────────────────────────────┘
```

## Phase 1: Strip to Core (Current Sprint)

Remove external service dependencies from the default path:

| Service | Replacement | Impact |
|---------|------------|--------|
| Prometheus | Structured JSON logging | Loses metrics dashboard, gains simplicity |
| Grafana | n/a (moot if Prometheus removed) | — |
| Focalboard | Markdown task files in `.half/tasks/` | Loses Kanban UI, gains git-traceable tasks |
| PostgreSQL | SQLite via `langgraph-checkpoint-sqlite` | Loses multi-user, gains zero-config |
| Agent Mail DB | SQLite (already is SQLite) | No change |

**Result**: A user can `pip install hermes-half` and run `half init && half run` with zero Docker dependencies.

## Phase 2: Modularize (Next Sprint)

```
src/half/
├── core/              # Phase engine, gates, fail-safe (keep)
│   ├── orchestrator.py
│   ├── gate_checker.py
│   └── fail_safe.py
├── agents/            # 16 agents (keep, reduce to 8)
├── state/             # LangGraph state (keep)
├── runtime/           # LangGraph graph, checkpointer (keep)
├── agent_mail/        # Inter-agent messaging (keep)
├── http_sidecar.py    # REST API (move to half-gui)
└── half_sidecar.py    # Tauri IPC (move to half-gui)
```

**Agent consolidation** (16 → 8):
- Merge `discovery` + `specification` + `architect` → `planner`
- Merge `scaffold` + `implement` + `simplify` → `builder`
- Merge `testing` + `security` + `integration` → `verifier`
- Merge `infrastructure` + `cicd` + `launch` → `deployer`
- Keep `iterate`, `observe`, `codify` separate

## Phase 3: CI/CD Cleanup (Backlog)

| Current Workflow | Action | 
|-----------------|--------|
| `ci.yml` | Keep — test + lint core |
| `cd.yml` | Merge into ci.yml |
| `integration.yml` | Keep for integration tests |
| `release.yml` | Keep |
| `security-scan.yml` | Merge into ci.yml |

## Action Items

### P0 — This Week
- [ ] Make SQLite the default checkpoint backend (remove PostgreSQL requirement)
- [ ] Replace Prometheus/Grafana with structured logging
- [ ] Replace Focalboard with `.half/tasks/` markdown files
- [ ] Remove `docker compose` from quickstart path
- [ ] Update README: "Quick Start" should not mention Docker

### P1 — Next Sprint
- [ ] Consolidate 16 agents into 8
- [ ] Move HTTP sidecar into optional `half serve` CLI command
- [ ] Move Tauri GUI into separate repo
- [ ] Reduce CI from 5 workflows to 3

### P2 — Backlog
- [ ] Replace `langgraph` with simpler state machine (reduce dependency weight)
- [ ] Create `hermes-half-gui` standalone repo
- [ ] Remove CVE-pinned hack in LangGraph SQLite (upstream fix)

## Measuring Success

| Metric | Before | After (target) |
|--------|--------|---------------|
| Source lines | 10,388 | <5,000 |
| Service dependencies | 5 | 0 (optional) |
| CI workflows | 5 | 3 |
| Install steps | git clone + setup.sh + Docker | pip install |
| Time to first `half run` | ~15 min | <2 min |
