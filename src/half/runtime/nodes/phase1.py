"""Phase 1: Discovery & Strategy nodes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from half.runtime.nodes._write_artifact import _write_artifact

if TYPE_CHECKING:
    from half.runtime.state import HalfState

logger = logging.getLogger("half.runtime.nodes")


def phase_1_discovery(state: HalfState) -> dict[str, Any]:
    """Phase 1A: Requirements discovery.

    Uses the DiscoveryAgent with LLM provider to analyze the project
    concept and generate structured requirements. Falls back to template
    text if the LLM is unavailable.
    """
    from half.agents.discovery import DiscoveryAgent

    project = state.get("project_name", "default")
    logger.info("Phase 1A: Requirements discovery for '%s'", project)

    # Use the DiscoveryAgent with the configured LLM provider
    agent = DiscoveryAgent(project_name=project)
    concept = state.get("project_concept", project)

    try:
        doc = agent.analyze_with_llm(concept)
        content = doc.render_markdown()  # type: ignore[attr-defined]
        source = "llm"
        logger.info("DiscoveryAgent LLM analysis succeeded for '%s'", project)
    except Exception:
        logger.exception(
            "LLM analysis failed for '%s', using template fallback", project
        )
        # Graceful fallback: use the standard template
        content = f"""# Requirements: {project}

## Elevator Pitch
{concept}

## Core Capabilities
| ID | Capability | Priority | Confidence |
|----|-----------|----------|------------|
| C-001 | [LLM unavailable -- populate manually] | P0 | HIGH |

## Target Users
- **Primary:** [User persona]
- **Secondary:** [User persona]

## Constraints
- **Timeline:** [TBD]
- **Tech preferences:** Python 3.13+
- **Compliance:** Standard

## Success Metrics
| Metric | Target | Method |
|--------|--------|--------|
| Uptime | 99.9% | Health monitoring |

## Non-Goals
1. [Out of scope item]

## Open Questions
- [Question needing human input]
"""
        source = "fallback"

    _write_artifact("phase-1", "01-REQUIREMENTS.md", content)
    return {
        "current_step": "phase-1-discovery",
        "artifacts": [
            *state.get("artifacts", []),
            {"name": "01-REQUIREMENTS.md", "phase": "phase-1"},
        ],
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 1A: REQUIREMENTS.md generated ({source})",
            }
        ],
    }


def phase_1_specification(state: HalfState) -> dict[str, Any]:
    """Phase 1B: Technical specification generation."""
    project = state.get("project_name", "default")
    logger.info("Phase 1B: Specification for '%s'", project)

    content = f"""# Technical Specification: {project}

## Functional Requirements
### FR-001: Core Feature
**Priority:** P0 | **Estimate:** 2-4h
**Description:** [Feature description]
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

## Non-Functional Requirements
| ID | Category | Target |
|----|----------|--------|
| NFR-001 | Performance | <200ms p95 |
| NFR-002 | Security | OWASP Top 10 |
| NFR-003 | Observability | Health + metrics endpoints |

## API Contracts
### POST /api/v1/resource
**Request:** {{field: type}}
**Response 200:** {{id: string}}
**Errors:** 400, 401, 404

## Data Model
### Entity
- id: UUID (PK)
- created_at: datetime
- updated_at: datetime
"""
    _write_artifact("phase-1", "02-SPECIFICATION.md", content)

    # Task decomposition
    tasks = f"""# Task Decomposition: {project}

| ID | Name | Dependencies | Estimate |
|----|------|-------------|----------|
| T-001 | Scaffold project | None | 30m |
| T-002 | Implement core | T-001 | 4h |
| T-003 | Add tests | T-002 | 2h |
"""
    _write_artifact("phase-1", "03-TASKS.md", tasks)

    iteration = state.get("iteration_count", 0) + 1
    return {
        "current_step": "phase-1-specification",
        "iteration_count": iteration,
        "messages": [
            {
                "role": "assistant",
                "content": "Phase 1B: Specification and tasks generated",
            }
        ],
    }


def phase_1_architecture(state: HalfState) -> dict[str, Any]:
    """Phase 1C: Ideal State Architecture with ADRs."""
    project = state.get("project_name", "default")
    logger.info("Phase 1C: Architecture for '%s'", project)

    arch = f"""# Architecture: {project}

## System Diagram
```mermaid
graph TB
    Client[Client] --> API[API Gateway]
    API --> Service[Core Service]
    Service --> DB[(Database)]
    Service --> Cache[(Cache)]
```

## Component Design
| Component | Responsibility |
|-----------|---------------|
| API Gateway | Auth, routing, rate limiting |
| Core Service | Business logic |
| Database | Persistent storage |

## Security Architecture
- Auth: JWT with HTTP-only cookies
- Encryption: TLS 1.3 in transit, AES-256 at rest
- Rate limiting: 100 req/min per user
"""
    _write_artifact("phase-1", "04-ARCHITECTURE.md", arch)

    adrs = """# Architecture Decision Records

## ADR-001: Database
**Context:** Need persistent storage
**Decision:** PostgreSQL 17
**Alternatives:** SQLite, MongoDB
**Consequences:** ACID compliance, pgvector support
"""
    _write_artifact("phase-1", "05-ADRs.md", adrs)

    return {
        "current_step": "phase-1-architecture",
        "messages": [
            {
                "role": "assistant",
                "content": "Phase 1C: Architecture and ADRs generated",
            }
        ],
    }


def phase_1_gate(state: HalfState) -> dict[str, Any]:
    """Gate: Phase 1 completeness -- verifies all 5 artifacts exist."""
    logger.info("Phase 1: Gate check")
    from half import config as half_config

    artifacts_dir = Path(half_config.ARTIFACTS_PHASE_1)
    required = [
        "01-REQUIREMENTS.md",
        "02-SPECIFICATION.md",
        "03-TASKS.md",
        "04-ARCHITECTURE.md",
        "05-ADRs.md",
    ]
    missing = [r for r in required if not (artifacts_dir / r).exists()]
    passed = len(missing) == 0

    return {
        "current_step": "phase-1-gate",
        "gate_results": [
            {
                "gate_id": "G1",
                "passed": passed,
                "details": f"Phase 1 artifacts: {len(required) - len(missing)}/{len(required)} present"
                + (f". Missing: {missing}" if missing else ""),
                "timestamp": datetime.now(tz=UTC).isoformat(),
            }
        ],
        "messages": [
            {
                "role": "assistant",
                "content": f"Phase 1 Gate: {'PASSED' if passed else 'FAILED'} - {missing}",
            }
        ],
    }
