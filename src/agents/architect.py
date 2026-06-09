"""
HALF-Architect Agent (Phase 1C)

Generates the Ideal State Architecture document with system diagrams,
component designs, ADRs, data flows, and security architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArchitectureDecisionRecord:
    id: str
    title: str
    context: str
    options: list[str]
    decision: str
    consequences_positive: list[str] = field(default_factory=list)
    consequences_negative: list[str] = field(default_factory=list)
    status: str = "Accepted"


@dataclass
class Component:
    name: str
    responsibility: str
    interfaces: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    failure_mode: str = ""


class ArchitectAgent:
    """Phase 1C: Ideal State Architecture generation."""

    def __init__(self):
        self.adrs: list[ArchitectureDecisionRecord] = []
        self.components: list[Component] = []
        self.architecture_description: str = ""

    def add_adr(
        self,
        title: str,
        context: str,
        options: list[str],
        decision: str,
        positive: list[str] | None = None,
        negative: list[str] | None = None,
    ) -> ArchitectureDecisionRecord:
        """Add an Architecture Decision Record."""
        adr_id = f"ADR-{len(self.adrs) + 1:03d}"
        record = ArchitectureDecisionRecord(
            id=adr_id,
            title=title,
            context=context,
            options=options,
            decision=decision,
            consequences_positive=positive or [],
            consequences_negative=negative or [],
        )
        self.adrs.append(record)
        return record

    def add_component(
        self,
        name: str,
        responsibility: str,
        interfaces: list[str] | None = None,
        dependencies: list[str] | None = None,
        failure_mode: str = "",
    ) -> Component:
        """Add a system component."""
        component = Component(
            name=name,
            responsibility=responsibility,
            interfaces=interfaces or [],
            dependencies=dependencies or [],
            failure_mode=failure_mode,
        )
        self.components.append(component)
        return component

    def generate_system_diagram(self) -> str:
        """Generate a Mermaid system architecture diagram."""
        lines = [
            "```mermaid",
            "graph TB",
            "    subgraph Client Layer",
        ]

        # Client components
        clients = [
            c
            for c in self.components
            if "client" in c.name.lower() or "ui" in c.name.lower()
        ]
        for c in clients:
            lines.append(f"        {c.name}[{c.name}]")

        if not clients:
            lines.append("        Web[Web Client]")
            lines.append("        Mobile[Mobile Client]")

        lines.extend(
            [
                "    end",
                "",
                "    subgraph API Layer",
            ]
        )

        apis = [
            c
            for c in self.components
            if "api" in c.name.lower() or "gateway" in c.name.lower()
        ]
        for c in apis:
            lines.append(f"        {c.name}[{c.name}]")

        if not apis:
            lines.append("        API[API Gateway]")

        lines.extend(
            [
                "    end",
                "",
                "    subgraph Service Layer",
            ]
        )

        services = [c for c in self.components if c not in clients and c not in apis]
        for c in services:
            lines.append(f"        {c.name}[{c.name}]")

        if not services:
            lines.append("        Auth[Auth Service]")
            lines.append("        Core[Core Service]")

        lines.extend(
            [
                "    end",
                "",
                "    subgraph Data Layer",
                "        DB[(Primary Database)]",
                "        Cache[(Cache)]",
                "        Queue[(Message Queue)]",
                "    end",
            ]
        )

        # Connections
        for c in self.components:
            for dep in c.dependencies:
                lines.append(f"    {c.name} --> {dep}")

        if not self.components:
            lines.extend(
                [
                    "    Web --> API",
                    "    Mobile --> API",
                    "    API --> Auth",
                    "    API --> Core",
                    "    Auth --> DB",
                    "    Core --> DB",
                    "    Core --> Cache",
                    "    API --> Queue",
                ]
            )

        lines.append("```")
        return "\n".join(lines)

    def render_adrs_markdown(self) -> str:
        """Render all ADRs as markdown."""
        lines = ["# Architecture Decision Records", ""]
        for adr in self.adrs:
            lines.extend(
                [
                    f"## {adr.id}: {adr.title}",
                    "",
                    f"**Status:** {adr.status}",
                    "",
                    "### Context",
                    adr.context,
                    "",
                    "### Options Considered",
                ]
            )
            for opt in adr.options:
                lines.append(f"1. {opt}")
            lines.extend(
                [
                    "",
                    "### Decision",
                    adr.decision,
                    "",
                    "### Consequences",
                ]
            )
            lines.append("**Positive:**")
            for c in adr.consequences_positive:
                lines.append(f"- {c}")
            lines.append("**Negative:**")
            for c in adr.consequences_negative:
                lines.append(f"- {c}")
            lines.append("")
        return "\n".join(lines)

    def render_architecture_markdown(self) -> str:
        """Render the full architecture document as markdown."""
        lines = [
            "# Ideal State Architecture",
            "",
            "## System Architecture",
            "",
            self.generate_system_diagram(),
            "",
            "## Component Design",
            "",
            "| Component | Responsibility | Interfaces | Dependencies | Failure Mode |",
            "|-----------|---------------|------------|-------------|-------------|",
        ]
        for c in self.components:
            ifaces = ", ".join(c.interfaces) or "-"
            deps = ", ".join(c.dependencies) or "-"
            fm = c.failure_mode or "Not documented"
            lines.append(
                f"| {c.name} | {c.responsibility} | {ifaces} | {deps} | {fm} |"
            )

        lines.extend(
            [
                "",
                "## Security Architecture",
                "",
                "### Authentication & Authorization",
                "- **Auth Model:** JWT-based with HTTP-only cookies",
                "- **Authorization:** RBAC with ownership-based access",
                "- **Password Hashing:** bcrypt (cost factor ≥ 12)",
                "",
                "### Data Protection",
                "- **In Transit:** TLS 1.3",
                "- **At Rest:** AES-256 encryption for sensitive fields",
                "- **PII:** Field-level encryption with envelope keys",
                "",
                "### Rate Limiting",
                "- **Per-User:** 100 req/min per endpoint group",
                "- **Per-IP:** 1000 req/min",
                "- **Burst Allowance:** 2x for 10s windows",
                "",
                "## Data Flow",
                "",
                "### Write Path",
                "1. Client -> API Gateway -> Service -> Validation -> Database -> Response",
                "",
                "### Read Path",
                "1. Client -> API Gateway -> Cache (if hit) OR Service -> Database -> Response",
            ]
        )
        return "\n".join(lines)
