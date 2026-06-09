---
name: half
description: "Hermes Agentic Lifecycle Framework (HALF) — transforms a high-level business concept into a production-ready, user-installed software product. Covers Discovery & Strategy, Development & Coding, Quality Assurance, Polish & Deployment, and Iteration with autonomous agent workflows, guardrails, and fail-safe protocols for each phase."
version: 1.0.0
author: Hermes Agent / Turin Tech Solutions
license: MIT
platforms: [linux, macos]
metadata:
  tags: [half, lifecycle, sdlc, agentic-se, production, deployment, qa, strategy]
---

# HALF — Hermes Agentic Lifecycle Framework

## Overview

**HALF** is a modular, template-ready framework that enables Hermes Agent to autonomously execute the full software development lifecycle — from a high-level business concept through to a production-ready, user-installed software product. This repository contains the complete framework implementation.

**Core philosophy:** The agent executes phases autonomously within defined guardrails. The human defines intent, sets quality thresholds, reviews checkpoints, and owns product decisions. The agent never proceeds if current outputs deviate from established performance benchmarks — fail-safe protocols halt the pipeline and report exactly what breached.

### The Five Phases

```
CONCEPT → [PHASE 1: Discovery & Strategy] → Technical Spec + Ideal State Architecture
         → [PHASE 2: Development & Coding] → Modular, pattern-adherent codebase
         → [PHASE 3: Quality Assurance]     → Tests + Security + Red-Teaming
         → [PHASE 4: Polish & Deployment]   → Infra + CI/CD + Launch State
         → [PHASE 5: Iteration]            → Feedback Loops + QoL Updates
                                              ↓
                                  PRODUCTION SOFTWARE PRODUCT
```

**Three Human Checkpoints (non-negotiable):**
1. **After Phase 1** — Review the spec and architecture before code is written
2. **After Phase 3** — Review test results, security findings, and merge confidence
3. **After Phase 4** — Review launch readiness, rollback plan, and monitoring

---

## PHASE 1: Discovery & Strategy

**Objective:** Transform a high-level business concept into a formal technical specification and an "Ideal State" architecture document precise enough for autonomous implementation.

### 1A. Requirements Discovery Workflow

**Trigger:** User provides a business concept, feature request, or product idea.

**Agent Skill: HALF-Discovery**

```
1. RECEIVE input concept from user
2. EXPAND the concept via structured inquiry:
   - Core capabilities (what must the system DO?)
   - Target users (who uses this? primary + secondary personas)
   - Constraints (timeline, budget, compliance, tech stack preferences)
   - Success metrics (how do we know it worked?)
   - Non-goals (what is explicitly NOT in scope)

3. AMBIGUITY RESOLUTION:
   - For each requirement identified, rate confidence: HIGH / MEDIUM / LOW
   - For LOW confidence items, generate specific clarifying questions
   - Present to human at checkpoint if ambiguity would block design
   - If no clarification available, make documented conservative default

4. OUTPUT: .hale/artifacts/phase-1/01-REQUIREMENTS.md
```

**Template: Requirements Document:**
```markdown
# Requirements: [PROJECT NAME]

## Elevator Pitch
[One paragraph — what this is, who it's for, why it exists]

## Core Capabilities
| ID | Capability | Priority | Confidence | Clarification Needed |
|----|-----------|----------|------------|---------------------|
| C-001 | [capability] | P0/P1/P2 | HIGH/MED/LOW | [notes if any] |

## Target Users
- **Primary:** [persona — role, technical level, goals]
- **Secondary:** [persona]

## Constraints
- Timeline: [date or duration]
- Tech preferences: [languages, frameworks, hosting hinted at]
- Compliance: [GDPR, SOC2, HIPAA, none — be explicit]
- Budget: [infra cost limits if any]

## Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| [metric] | [value] | [how to measure] |

## Non-Goals (Explicitly Out of Scope for v1)
1. [thing we are not building]
2. [thing we are not building]

## Open Questions
- [question that needs human decision]
```

### 1B. Technical Specification Generation

**Agent Skill: HALF-Specification**

```
1. LOAD requirements from 01-REQUIREMENTS.md
2. GENERATE formal specification covering:
   a. FUNCTIONAL REQUIREMENTS (numbered FR-XXX)
   b. NON-FUNCTIONAL REQUIREMENTS (NFR-XXX)
   c. API CONTRACTS (endpoints, request/response schemas, error codes)
   d. DATA MODEL (entities, fields, types, constraints, relationships)
   e. STATE MACHINES (states, transitions, guards, actions)

3. SAVE to .hale/artifacts/phase-1/02-SPECIFICATION.md

4. TASK DECOMPOSITION:
   - Break specification into implementable tasks
   - Each task: ID, name, files to create/modify, acceptance criteria, dependencies
   - Dependency graph (tasks with 0 dependencies = parallelizable)
   - SAVE to .hale/artifacts/phase-1/03-TASKS.md
```

### 1C. Ideal State Architecture (ISA)

**Agent Skill: HALF-Architect**

```
1. LOAD specification from 02-SPECIFICATION.md
2. GENERATE Ideal State Architecture document:
   a. SYSTEM DIAGRAM (Mermaid/ASCII)
   b. COMPONENT DESIGN
   c. TECHNOLOGY DECISIONS (ADRs — at least 3)
   d. DATA FLOW DIAGRAMS
   e. SECURITY ARCHITECTURE

3. SAVE to .hale/artifacts/phase-1/04-ARCHITECTURE.md
4. SAVE ADRs to .hale/artifacts/phase-1/05-ADRs.md
```

### Phase 1 Gate Check
- G1.1: All core capabilities have corresponding FR-IDs
- G1.2: Each FR has acceptance criteria
- G1.3: Architecture decisions have ADRs with alternatives (≥3)
- G1.4: Task dependency graph has no circular dependencies
- G1.5: Non-functional requirements include security + observability

---

## PHASE 2: Development & Coding

**Objective:** Implement the modular codebase following strict architectural patterns defined in Phase 1. TDD is mandatory.

### 2A. Repository Scaffolding

**Agent Skill: HALF-Scaffold**

```
1. LOAD task decomposition from 03-TASKS.md
2. CREATE repository structure:
   - pyproject.toml / package.json / Cargo.toml
   - .gitignore, .editorconfig, README.md
   - AGENTS.md (project conventions)
   - Dockerfile / docker-compose.yml
   - src/[project]/ and tests/

3. CONFIGURE quality tooling:
   - Linter (ruff, eslint)
   - Formatter (ruff format, prettier)
   - Type checker (mypy, tsc --strict)
   - Test runner (pytest, vitest, cargo test)
   - Pre-commit hooks (lint + format check)

4. CONFIGURE CI/CD (GitHub Actions / GitLab CI)
```

### 2B. Implementation Workflow

**Agent Skill: HALF-Implement**

**CORE PROTOCOL — Harness-First:**

For each task in dependency order:

1. **LOAD context** — spec, existing code, AGENTS.md
2. **WRITE TEST HARNESS FIRST** — failing test (RED)
3. **IMPLEMENT CODE** — make tests pass (GREEN)
4. **VERIFY** — tests pass, lint 0, type check 0, coverage ≥80%
5. **COMMIT** — `feat: [scope] — [task name]` referencing FR-IDs
6. **MOVE TO NEXT TASK**

### 2C. Parallel Execution Pattern
- Dispatch: spawn sub-agents for tasks with 0 unresolved dependencies
- Concurrency: up to max_concurrent_children
- When a task completes: resolve dependents, re-check ready queue

### 2D. Architecture Drift Detection
- If implementation reveals architecture needs adjustment:
  - **Trivial drift** → update ARCHITECTURE.md directly
  - **Significant drift** → write ADR, flag downstream tasks, HUMAN CHECKPOINT

### Phase 2 Gate Check
- G2.1: All FR-IDs have corresponding implementation
- G2.2: All tasks have passing tests
- G2.3: Lint passes with 0 errors
- G2.4: Type check passes (strict mode)
- G2.5: Coverage ≥80%
- G2.6: No circular imports

---

## PHASE 3: Quality Assurance

**Objective:** Ensure correctness, security, and robustness through comprehensive automated testing, adversarial red-teaming, and security hardening.

### 3A. Test Suite Completeness

**Agent Skill: HALF-Testing**

```
1. LOAD spec and existing test suite
2. GENERATE coverage matrix per FR:
   - Happy path test? ✓/✗
   - Each error condition test? ✓/✗
   - Each edge case test? ✓/✗
   - Property-based test? ✓/✗

3. FOR each gap: generate test, run, verify
4. GENERATE test quality report
```

### 3B. Autonomous Red-Teaming & Security Hardening

**Agent Skill: HALF-Security**

**3B.1 Automated Scan:**
- Bandit (Python SAST)
- Semgrep (cross-language)
- Trivy (dependency vulns)
- TruffleHog (secrets)

**3B.2 Adversarial Red-Teaming (4 parallel agents):**
- Pentester — web app vulns
- Cryptographer — auth, session, token security
- Infrastructure — Docker, CI/CD, CORS
- AI/Model Security — prompt injection, data poisoning

**Fix-As-You-Go:**
- Auto-fix CRITICAL/HIGH findings
- Verify with linters and type checkers
- Push directly to feature branch

### 3C. Integration & Contract Tests

**Agent Skill: HALF-Integration**

- Integration tests (complete user journeys)
- Contract tests (schema verification against spec)
- Load tests (spike + soak)
- Failure mode tests (kill DB, verify graceful degradation)

### Phase 3 Gate Check
- G3.1: Coverage ≥80% line, ≥70% branch
- G3.2: All FR-IDs have at least one test
- G3.3: No CRITICAL security findings unresolved
- G3.4: No HIGH findings unresolved (or documented exceptions)
- G3.5: All integration tests pass
- G3.6: Contract tests match spec
- G3.7: No secrets in codebase

---

## PHASE 4: Polish & Deployment

**Objective:** Infrastructure optimization, CI/CD integration, and ensuring a user-ready launch state.

### 4A. Infrastructure as Code

**Agent Skill: HALF-Infrastructure**

- Docker Compose (multi-stage, layer caching, distroless)
- Kubernetes manifests (deployment, service, ingress, HPA)
- Database migrations validated (dry-run)
- .env.example with all required env vars
- Health check endpoints configured

### 4B. CI/CD Pipeline Integration

**Agent Skill: HALF-CICD**

- GitHub Actions: test → security → build with per-stage gates
- CD pipeline: deploy-staging → smoke-test → deploy-production (manual approval)
- Rollback plan documented

### 4C. Production Readiness Checklist

**Agent Skill: HALF-Launch**

18-item checklist including:
- CI checks pass, Docker image built, migrations validated
- Rollback plan documented, monitoring configured
- Health checks operational, backup strategy implemented
- Rate limiting, CORS, SSL, error tracking, log aggregation verified

### Phase 4 Gate Check
- G4.1: All CI checks passing on main
- G4.2: Docker build succeeds (image <500MB)
- G4.3: Health endpoint returns 200
- G4.4: Smoke tests pass
- G4.5: Rollback plan exists
- G4.6: Monitoring endpoints exposed
- G4.7: No secrets in production config

---

## PHASE 5: Iteration

**Objective:** Implement feedback loops for continuous improvement and production issue resolution.

### 5A. Production Monitoring Loop

**Agent Skill: HALF-Observe**

- Metric collection: every 15m
- Log analysis: every 1h
- Health check: every 5m
- Anomaly detection: every 1h

### 5B. Issue Tracking & Triage

**Agent Skill: HALF-Iterate**

- Classify: Bug / Feature / Improvement / Tech Debt / Incident
- Bugs: reproduce → root cause → fix (TDD) → PR
- Features: mini-spec → estimate → implement
- Tech Debt: document → prioritize → fix

### 5C. The Codification Imperative (L3.5 → L4 Transition)

**Agent Skill: HALF-Codify**

When a human overrides or corrects an agent action:
1. WHAT was the correction?
2. WHY was the agent wrong?
3. HOW can the agent avoid this next time?

The answer becomes: AGENTS.md update, new/updated skill, HALF workflow update, or new test case.

### 5D. Continuous Quality-of-Life Updates

- Weekly dependency check (uv pip list --outdated)
- Weekly coverage trend check
- Per-PR spec drift detection
- Monthly skill refresh

### Phase 5 Gate Check
- G5.1: Monitoring loop is active
- G5.2: Issue triage workflow documented
- G5.3: No HIGH/CRITICAL issues unresolved >7 days
- G5.4: Codification Imperative is active

---

## Fail-Safe Protocol (Global)

```yaml
fail_safe:
  enabled: true
  max_retries: 3
  escalation_path:
    - 0: "auto-remediate (re-run failed step)"
    - 1: "auto-remediate with broader scope (re-run phase)"
    - 2: "human checkpoint required (generate gap report)"
    - 3: "abort pipeline — insufficient progress"
  circuit_breakers:
    - ">5 test suites fail in same run → halt phase 2"
    - "CRITICAL security finding → halt phase 3"
    - "Docker build fails after 3 retries → halt phase 4"
    - "coverage drops >5% → warn before proceeding"
```

## Error Budget

```yaml
error_budget:
  window: 30 days
  total: 100 points
  deductions:
    phase_1_failure: -5
    phase_2_failure: -10
    phase_3_failure: -15
    phase_4_failure: -20
    production_incident: -25
  thresholds:
    warning: "<40% — increase gate strictness"
    critical: "<20% — pause automation, human review"
    exhausted: "0% — full pipeline review required"
```

---

## Quick Reference: Agent Skills Map

| Phase | Agent Skill | Key Tools | Outputs |
|-------|-------------|-----------|---------|
| 1A | HALF-Discovery | web_search, read_file, write_file | REQUIREMENTS.md |
| 1B | HALF-Specification | write_file, delegate_task | SPECIFICATION.md, TASKS.md |
| 1C | HALF-Architect | write_file, delegate_task | ARCHITECTURE.md, ADRs |
| 2A | HALF-Scaffold | terminal, write_file | Repo structure, configs |
| 2B | HALF-Implement | terminal, delegate_task | Implemented features |
| 3A | HALF-Testing | terminal, search_files | Test coverage, quality report |
| 3B | HALF-Security | terminal, delegate_task | Security scan, red-team report |
| 3C | HALF-Integration | terminal, process, curl | Integration test report |
| 4A | HALF-Infrastructure | write_file, terminal | Docker/k8s configs |
| 4B | HALF-CICD | write_file, gh CLI | CI/CD pipelines |
| 4C | HALF-Launch | terminal, curl, gh | Readiness checklist, rollback |
| 5A | HALF-Observe | cronjob, terminal | Monitoring loops |
| 5B | HALF-Iterate | gh issue, write_file | Fixes, improvements |
| 5C | HALF-Codify | skill_manage, memory | Skill/AGENTS.md updates |
