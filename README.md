<div align="center">

# HALF — Hermes Agentic Lifecycle Framework

**Transform high-level business concepts into production-ready software through autonomous, multi-agent orchestration.**

[![CI](https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](pyproject.toml)

</div>

---

## What is HALF?

**HALF** is a modular, template-driven framework that enables an AI agent to autonomously execute the full software development lifecycle — from a high-level business concept through to a production-ready, user-installed software product.

It implements the **5-phase structured SDLC** with built-in quality gates, fail-safe protocols, and explicit human checkpoints:

```
CONCEPT → [PHASE 1] Discovery & Strategy   → Technical Spec + Architecture
         → [PHASE 2] Development & Coding   → Modular, tested codebase
         → [PHASE 3] Quality Assurance       → Tests + Security + Red-Teaming
         → [PHASE 4] Polish & Deployment     → IaC + CI/CD + Launch State
         → [PHASE 5] Iteration              → Feedback Loops + QoL Updates
```

---

## Core Principles

- **Agent executes, human directs** — Agents handle implementation; humans set intent, review checkpoints, and own product decisions
- **Gates before progress** — Every phase has mandatory quality gates; no phase starts until the previous one passes
- **Fail-safe by design** — 3-level escalation: step retry → phase retry → human gap report
- **TDD is mandatory** — Harness-first: write failing tests before any implementation code
- **Codification Imperative** — Every manual fix becomes a durable improvement to the agent system

---

## Repository Structure

```
Hermes-Agentic-Lifecycle-Framework/
├── SKILL.md                  # Core framework doctrine
├── AGENTS.md                 # Agent context for this repo
├── README.md                 # You are here
├── LICENSE                   # MIT license
├── pyproject.toml            # Python project config
│
├── src/                      # Python implementation
│   ├── state/                # LangGraph state machine (CVE-2025-67644 mitigated)
│   ├── core/                 # Orchestrator, gates, fail-safes, error budget
│   └── agents/               # 16 agent skill implementations
│       ├── discovery.py      # HALF-Discovery (Phase 1A)
│       ├── specification.py  # HALF-Specification (Phase 1B)
│       ├── architect.py      # HALF-Architect (Phase 1C)
│       ├── scaffold.py       # HALF-Scaffold (Phase 2A)
│       ├── implement.py      # HALF-Implement (Phase 2B)
│       ├── testing.py        # HALF-Testing (Phase 3A)
│       ├── security.py       # HALF-Security (Phase 3B)
│       ├── integration.py    # HALF-Integration (Phase 3C)
│       ├── infrastructure.py # HALF-Infrastructure (Phase 4A)
│       ├── cicd.py           # HALF-CICD (Phase 4B)
│       ├── launch.py         # HALF-Launch (Phase 4C)
│       ├── observe.py        # HALF-Observe (Phase 5A)
│       ├── iterate.py        # HALF-Iterate (Phase 5B)
│       └── codify.py         # HALF-Codify (Phase 5C)
│
├── references/               # Quick-start guides
│   └── quickstart-execution.md
│
├── templates/                # Reusable templates
│   ├── fail-safes.yaml       # 3-level escalation config
│   └── gap-report.md         # Consultation Request Pack template
│
├── config/                   # Example configurations
│   ├── goal.yaml.example     # Goal CLI orchestration config
│   └── lm-studio.yaml.example # LM Studio AMD ROCm config
│
├── examples/                 # Example output walkthroughs
│   └── api-service/
│       └── phase-1/          # Phase 1 artifacts for a sample project
│
├── scripts/                  # Utility and bootstrap scripts
│   ├── bootstrap.sh          # Initialize .hale workspace
│   ├── run-phase.sh          # Execute a specific phase
│   ├── gate-check.sh         # Run phase gate checks
│   └── deploy.sh             # Deployment helper
│
├── docker/                   # Container builds
│   ├── Dockerfile            # Multi-stage build
│   └── docker-compose.yml    # Local services
│
└── .github/workflows/        # CI/CD pipelines
    ├── ci.yml                # PR quality gates
    ├── cd.yml                # Deployment pipeline
    └── security-scan.yml     # Weekly security audit
```

---

## Quick Start

### Prerequisites

- **Python 3.13+** — Runtime for the framework
- **Hermes Agent** — The execution environment ([docs](https://hermes-agent.nousresearch.com/docs))
- **git** — Version control
- **uv** (recommended) or pip — Package manager

### Run HALF on Your Project

```bash
# 1. Clone this repo
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework

# 2. (Optional) Install Python deps for local tooling
pip install uv
uv sync --group dev

# 3. Bootstrap the workspace
./scripts/bootstrap.sh

# 4. In your Hermes Agent session:
skill_view(name="half")
```

Then follow the **5-phase execution sequence** defined in `SKILL.md`.

---

## The 5 Phases

### Phase 1: Discovery & Strategy
**Objective:** Transform a business concept into a precise technical specification.

| Step | Agent Skill | Key Actions |
|------|-------------|-------------|
| 1A | HALF-Discovery | Expand concept, rate confidence, resolve ambiguity |
| 1B | HALF-Specification | Generate FRs, NFRs, API contracts, data model |
| 1C | HALF-Architect | System diagram, components, ADRs, security architecture |

**Gate:** Completeness checks on all 5 artifacts → **Human checkpoint**

### Phase 2: Development & Coding
**Objective:** Implement the codebase with mandatory TDD.

| Step | Agent Skill | Key Actions |
|------|-------------|-------------|
| 2A | HALF-Scaffold | Repo structure, tooling config, CI setup |
| 2B | HALF-Implement | Harness-first TDD, parallel dependency dispatch |

**Gate:** Tests pass, lint 0, types 0, coverage ≥80%

### Phase 3: Quality Assurance
**Objective:** Ensure correctness, security, and robustness.

| Step | Agent Skill | Key Actions |
|------|-------------|-------------|
| 3A | HALF-Testing | FR coverage matrix, gap test generation |
| 3B | HALF-Security | SAST scan + 4-agent red-teaming |
| 3C | HALF-Integration | Integration, contract, and load tests |

**Gate:** No CRITICAL security findings → **Human checkpoint**

### Phase 4: Polish & Deployment
**Objective:** Infrastructure, CI/CD, and production readiness.

| Step | Agent Skill | Key Actions |
|------|-------------|-------------|
| 4A | HALF-Infrastructure | Docker, k8s, serverless configs |
| 4B | HALF-CICD | CI/CD pipelines with per-stage gates |
| 4C | HALF-Launch | 18-item readiness checklist, rollback plan |

**Gate:** Health endpoint, smoke tests, MRP generated → **Human signature**

### Phase 5: Iteration
**Objective:** Continuous improvement and production monitoring.

| Step | Agent Skill | Key Actions |
|------|-------------|-------------|
| 5A | HALF-Observe | Monitoring loops, anomaly detection |
| 5B | HALF-Iterate | Issue triage, feature/bug workflow |
| 5C | HALF-Codify | Convert corrections into durable improvements |

**Gate:** Monitoring active, Codification Imperative active

---

## Fail-Safe Protocol

HALF implements a **3-level escalation** for any phase failure:

1. **Step Retry** (×3) — Auto-analyze failure, adjust approach, retry
2. **Phase Retry** (×2) — Re-run entire phase with expanded context
3. **Human Escalation** — Generate `Gap Report` (CRP), pause pipeline, wait for decision

```yaml
circuit_breakers:
  - ">5 test failures → halt phase 2"
  - "CRITICAL security finding → halt phase 3"
  - "coverage drops >5% → warn before proceeding"
```

## Error Budget

| Budget | 100 points / 30 days | |
|--------|----------------------|---|
| Gate failure | -5 to -20 points | (severity-dependent) |
| Production incident | -5 to -25 points | (P3 → P1) |
| Warning threshold | <40% | Tighten gates |
| Critical threshold | <20% | Pause automation |
| Exhausted | 0% | Full pipeline review |

---

## Modes

| Mode | Phases | Use Case |
|------|--------|----------|
| `full` | 1-5 | Complete lifecycle from concept to production |
| `prototype` | 1, 2, 4 | Quick validation (skip deep QA + iteration) |
| `patch` | 5 | Small fix on existing codebase |
| `audit` | 3, 5 | Security audit on existing code |

---

## Research Base (June 2026)

HALF is grounded in the following sources:

1. **Dash0 — Six Levels of Agentic SE** (Ben Blackmore, Jun 2026)
2. **Microsoft/GitHub — An AI-led SDLC** (Feb 2026)
3. **PwC — Agentic SDLC in Practice** (2026)
4. **arXiv 2604.10599 — Alenezi, Rethinking SE for Agentic AI** (2026)
5. **OWASP GenAI — Agentic Red Teaming, Q2 2026**
6. **Anthropic — 2026 Agentic Coding Trends Report**
7. **CIO/Wadhwa — How Agentic AI Reshapes Engineering Workflows** (Feb 2026)
8. **Hans Reinl — Agentic Engineering Across the SDLC** (2026)
9. **JetBrains — Top Agentic Frameworks 2026**
10. **OpenSearch — Harness-first Agentic SDLC** (May 2026)

---

## Contributing

This framework is designed to evolve. See the **Codification Imperative** section in `SKILL.md` for how to contribute improvements.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

---

## License

MIT — See [LICENSE](LICENSE) for details.

Built by [Turin Tech Solutions](mailto:josh@turintechsolutions.com) with Hermes Agent.
