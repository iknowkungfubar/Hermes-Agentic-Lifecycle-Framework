# Phase 1: Discovery & Strategy

**Objective:** Transform a high-level business concept into a formal technical specification and architecture.

## Steps

1. **1A: Requirements Discovery** — Expand concept, rate confidence, resolve ambiguity
2. **1B: Technical Specification** — Generate FRs, NFRs, API contracts, data model
3. **1C: Ideal State Architecture** — System diagram, components, ADRs, security

## Artifacts

- `01-REQUIREMENTS.md` — Capabilities, users, constraints, success metrics
- `02-SPECIFICATION.md` — Functional + non-functional requirements, API contracts
- `03-TASKS.md` — Task decomposition with dependency graph
- `04-ARCHITECTURE.md` — System architecture, component design, data flow
- `05-ADRs.md` — Architecture Decision Records (≥3)

## Gate Check (G1)

- G1.1: All capabilities have FR-IDs
- G1.2: Each FR has acceptance criteria
- G1.3: ADRs with alternatives (≥3)
- G1.4: Task DAG has no circular dependencies
- G1.5: NFRs include security + observability
