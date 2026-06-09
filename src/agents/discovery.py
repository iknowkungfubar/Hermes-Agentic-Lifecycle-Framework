"""
HALF-Discovery Agent (Phase 1A)

Receives a business concept and expands it into structured requirements
via structured inquiry. Handles ambiguity resolution and confidence rating.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Capability:
    id: str
    description: str
    priority: str  # P0, P1, P2
    confidence: str  # HIGH, MEDIUM, LOW
    clarification_needed: str | None = None


@dataclass
class RequirementDocument:
    project_name: str
    elevator_pitch: str
    capabilities: list[Capability] = field(default_factory=list)
    target_users: dict[str, str] = field(default_factory=dict)
    constraints: dict[str, str] = field(default_factory=dict)
    success_metrics: dict[str, str] = field(default_factory=dict)
    non_goals: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)


class DiscoveryAgent:
    """Phase 1A: Requirements discovery from a business concept."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.requirements = RequirementDocument(
            project_name=project_name, elevator_pitch=""
        )

    def expand_concept(
        self,
        concept: str,
        capabilities: list[dict[str, str]] | None = None,
        users: dict[str, str] | None = None,
        constraints: dict[str, str] | None = None,
    ) -> RequirementDocument:
        """Expand a high-level concept into structured requirements.

        Args:
            concept: The business concept or product idea.
            capabilities: Optional list of capability dicts.
            users: Optional dict of user personas.
            constraints: Optional dict of constraints.

        Returns:
            A populated RequirementDocument.
        """
        self.requirements.elevator_pitch = concept

        if capabilities:
            for i, cap in enumerate(capabilities):
                self.requirements.capabilities.append(
                    Capability(
                        id=f"C-{i + 1:03d}",
                        description=cap.get("description", ""),
                        priority=cap.get("priority", "P1"),
                        confidence=cap.get("confidence", "HIGH"),
                        clarification_needed=cap.get("clarification"),
                    )
                )

        if users:
            self.requirements.target_users = users

        if constraints:
            self.requirements.constraints = constraints

        return self.requirements

    def find_ambiguities(self) -> list[str]:
        """Find LOW confidence items that need clarification.

        Returns:
            List of clarifying questions for low-confidence capabilities.
        """
        questions = []
        for cap in self.requirements.capabilities:
            if cap.confidence in {"LOW", "MEDIUM"}:
                questions.append(
                    f"Q: '{cap.description}' — "
                    f"More detail needed on scope, behavior, or constraints?"
                )
        return questions

    def render_markdown(self) -> str:
        """Render the requirement document as markdown."""
        lines: list[str] = [
            f"# Requirements: {self.requirements.project_name}",
            "",
            "## Elevator Pitch",
            self.requirements.elevator_pitch,
            "",
            "## Core Capabilities",
            "| ID | Capability | Priority | Confidence |",
            "|----|-----------|----------|------------|",
        ]
        for cap in self.requirements.capabilities:
            clarification = cap.clarification_needed or ""
            lines.append(
                f"| {cap.id} | {cap.description} | {cap.priority} | "
                f"{cap.confidence} | {clarification} |"
            )

        lines.extend(
            [
                "",
                "## Target Users",
            ]
        )
        for role, desc in self.requirements.target_users.items():
            lines.append(f"- **{role}:** {desc}")

        lines.extend(
            [
                "",
                "## Constraints",
            ]
        )
        for key, val in self.requirements.constraints.items():
            lines.append(f"- **{key}:** {val}")

        lines.extend(
            [
                "",
                "## Success Metrics",
            ]
        )
        for metric, target in self.requirements.success_metrics.items():
            lines.append(f"- **{metric}:** {target}")

        lines.extend(
            [
                "",
                "## Non-Goals (Explicitly Out of Scope for v1)",
            ]
        )
        for ng in self.requirements.non_goals:
            lines.append(f"1. {ng}")

        lines.extend(
            [
                "",
                "## Open Questions",
            ]
        )
        for q in self.requirements.open_questions:
            lines.append(f"- {q}")

        return "\n".join(lines)
