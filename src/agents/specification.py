"""
HALF-Specification Agent (Phase 1B)

Generates formal technical specifications from requirements,
including FRs, NFRs, API contracts, data models, and task decomposition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FunctionalRequirement:
    id: str
    name: str
    priority: str
    depends_on: list[str]
    description: str
    acceptance_criteria: list[str]
    files_to_create: list[str] = field(default_factory=list)


@dataclass
class NonFunctionalRequirement:
    id: str
    category: str  # performance, security, scalability, observability
    description: str
    target: str


@dataclass
class APIContract:
    method: str
    path: str
    request_schema: dict[str, Any]
    response_schema: dict[str, Any]
    error_codes: list[dict[str, Any]]


@dataclass
class Task:
    id: str
    name: str
    fr_ids: list[str]
    files_to_create: list[str] = field(default_factory=list)
    files_to_modify: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimate: str = "2-4h"


class SpecificationAgent:
    """Phase 1B: Generate formal specifications from requirements."""

    def __init__(self):
        self.functional_reqs: list[FunctionalRequirement] = []
        self.non_functional_reqs: list[NonFunctionalRequirement] = []
        self.api_contracts: list[APIContract] = []
        self.tasks: list[Task] = []

    def add_functional_requirement(
        self,
        name: str,
        description: str,
        priority: str = "P1",
        depends_on: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        files_to_create: list[str] | None = None,
    ) -> FunctionalRequirement:
        """Add a functional requirement and derive FR-ID."""
        fr_id = f"FR-{len(self.functional_reqs) + 1:03d}"
        req = FunctionalRequirement(
            id=fr_id,
            name=name,
            priority=priority,
            depends_on=depends_on or [],
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            files_to_create=files_to_create or [],
        )
        self.functional_reqs.append(req)
        return req

    def add_non_functional_requirement(
        self,
        category: str,
        description: str,
        target: str,
    ) -> NonFunctionalRequirement:
        """Add a non-functional requirement."""
        nfr_id = f"NFR-{len(self.non_functional_reqs) + 1:03d}"
        req = NonFunctionalRequirement(
            id=nfr_id,
            category=category,
            description=description,
            target=target,
        )
        self.non_functional_reqs.append(req)
        return req

    def add_api_contract(
        self,
        method: str,
        path: str,
        request_schema: dict[str, Any],
        response_schema: dict[str, Any],
        error_codes: list[dict[str, Any]] | None = None,
    ) -> APIContract:
        """Add an API contract."""
        contract = APIContract(
            method=method.upper(),
            path=path,
            request_schema=request_schema,
            response_schema=response_schema,
            error_codes=error_codes or [],
        )
        self.api_contracts.append(contract)
        return contract

    def decompose_tasks(self) -> list[Task]:
        """Break specification into implementable tasks with dependency graph.

        Each FR becomes at least one task. Tasks with shared dependencies
        are grouped.
        """
        self.tasks = []
        for fr in self.functional_reqs:
            task = Task(
                id=f"T-{len(self.tasks) + 1:03d}",
                name=fr.name,
                fr_ids=[fr.id],
                files_to_create=fr.files_to_create,
                acceptance_criteria=fr.acceptance_criteria,
                dependencies=fr.depends_on,
                estimate=(fr.priority == "P0" and "1-2h") or "2-4h",
            )
            self.tasks.append(task)

        # Topological sort hint: group by dependency depth
        assigned: set[str] = set()
        ordered: list[Task] = []
        remaining = list(self.tasks)

        while remaining:
            ready = [t for t in remaining if all(d in assigned for d in t.dependencies)]
            if not ready:
                # Circular dependency — break it
                ready = [remaining[0]]
            for t in ready:
                ordered.append(t)
                assigned.add(t.id)
                remaining.remove(t)

        self.tasks = ordered
        return self.tasks

    def render_specification_markdown(self) -> str:
        """Render the full specification as markdown."""
        lines = ["# Technical Specification", ""]

        # FRs
        lines.extend(["## Functional Requirements", ""])
        for fr in self.functional_reqs:
            lines.extend(
                [
                    f"### {fr.id}: {fr.name}",
                    f"**Priority:** {fr.priority} | **Depends on:** {', '.join(fr.depends_on) or 'Nothing'} | **Estimate:** {(fr.priority == 'P0' and '1-2h') or '2-4h'}",
                    "",
                    f"**Description:** {fr.description}",
                    "",
                    "**Acceptance Criteria:**",
                ]
            )
            for ac in fr.acceptance_criteria:
                lines.append(f"- [ ] {ac}")
            if fr.files_to_create:
                lines.extend(["", "**Files:**"])
                for f in fr.files_to_create:
                    lines.append(f"- Create: {f}")
            lines.append("")

        # NFRs
        lines.extend(["## Non-Functional Requirements", ""])
        lines.append("| ID | Category | Description | Target |")
        lines.append("|----|----------|-------------|--------|")
        for nfr in self.non_functional_reqs:
            lines.append(
                f"| {nfr.id} | {nfr.category} | {nfr.description} | {nfr.target} |"
            )
        lines.append("")

        # API Contracts
        lines.extend(["## API Contracts", ""])
        for api in self.api_contracts:
            lines.extend(
                [
                    f"### {api.method} {api.path}",
                    "",
                    "**Request Schema:**",
                    f"```json\n{api.request_schema}\n```",
                    "",
                    "**Response Schema:**",
                    f"```json\n{api.response_schema}\n```",
                    "",
                    "**Error Codes:**",
                ]
            )
            for err in api.error_codes:
                lines.append(f"- {err.get('code')}: {err.get('description')}")
            lines.append("")

        return "\n".join(lines)

    def render_tasks_markdown(self) -> str:
        """Render task decomposition as markdown."""
        lines = [
            "# Task Decomposition",
            "",
            "| ID | Name | FRs | Files | Dependencies | Estimate |",
            "|----|------|-----|-------|-------------|----------|",
        ]
        for task in self.tasks:
            files = ", ".join(task.files_to_create + task.files_to_modify) or "-"
            deps = ", ".join(task.dependencies) or "-"
            lines.append(
                f"| {task.id} | {task.name} | "
                f"{', '.join(task.fr_ids)} | {files} | {deps} | {task.estimate} |"
            )
        lines.extend(
            [
                "",
                "## Dependency Graph (DAG)",
                "",
                "```mermaid",
                "graph TD",
            ]
        )
        for task in self.tasks:
            for dep in task.dependencies:
                lines.append(f"    {dep} --> {task.id}")
        lines.extend(["```", ""])
        return "\n".join(lines)
