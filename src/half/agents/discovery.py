"""
HALF-Discovery Agent (Phase 1A)

Receives a business concept and expands it into structured requirements
via structured inquiry. Handles ambiguity resolution and confidence rating.
Supports LLM-powered analysis via the provider abstraction layer.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from half.providers import ProviderRouter

logger = logging.getLogger("half.agents.discovery")


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
    """Phase 1A: Requirements discovery from a business concept.

    Uses an LLM (via the provider abstraction) to analyze concepts and
    generate structured requirement documents. Falls back to template-based
    expansion when the LLM is unavailable.
    """

    def __init__(self, project_name: str, router: ProviderRouter | None = None):
        self.project_name = project_name
        self.router = router or ProviderRouter()
        self.requirements = RequirementDocument(
            project_name=project_name, elevator_pitch=""
        )

    def analyze_with_llm(self, concept: str) -> RequirementDocument:
        """Analyze a concept using the configured LLM provider.

        Sends the concept to the LLM with a structured prompt that asks
        for elevator pitch, capabilities, target users, constraints,
        success metrics, non-goals, and open questions. Parses the JSON
        response into a populated RequirementDocument.

        Args:
            concept: The business concept or product idea.

        Returns:
            A populated RequirementDocument with LLM-generated content.
        """
        system_prompt = (
            "You are a senior product discovery analyst. "
            "Given a business concept, produce structured, actionable requirements. "
            "Output valid JSON only — no markdown fences, no extra text."
        )

        user_prompt = f"""Analyze the following concept and produce structured requirements.

Concept: {concept}

Return a JSON object with these exact keys:
- "elevator_pitch": string (1-2 sentences)
- "capabilities": list of objects with keys: "description", "priority" ("P0"/"P1"/"P2"), "confidence" ("HIGH"/"MEDIUM"/"LOW")
- "target_users": object with "primary" and "secondary" strings
- "constraints": object with any constraint keys (e.g., "timeline", "technology", "compliance")
- "success_metrics": object with metric names as keys and targets as values
- "non_goals": list of strings
- "open_questions": list of strings"""

        response = self.router.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            role="planner",
            temperature=0.4,
        )

        if not response:
            logger.warning(
                "LLM returned empty response for concept '%s' — using defaults",
                concept[:60],
            )
            self.requirements.elevator_pitch = concept
            return self.requirements

        try:
            data: dict[str, Any] = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown fences
            import re

            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    logger.warning(
                        "Could not parse LLM response as JSON — using defaults"
                    )
                    self.requirements.elevator_pitch = concept
                    return self.requirements
            else:
                logger.warning("Could not parse LLM response as JSON — using defaults")
                self.requirements.elevator_pitch = concept
                return self.requirements

        # Populate requirement document from parsed data
        self.requirements.elevator_pitch = data.get("elevator_pitch", concept)

        for i, cap in enumerate(data.get("capabilities", [])):
            self.requirements.capabilities.append(
                Capability(
                    id=f"C-{i + 1:03d}",
                    description=cap.get("description", ""),
                    priority=cap.get("priority", "P1"),
                    confidence=cap.get("confidence", "HIGH"),
                    clarification_needed=cap.get("clarification"),
                )
            )

        self.requirements.target_users = data.get("target_users", {})
        self.requirements.constraints = data.get("constraints", {})
        self.requirements.success_metrics = data.get("success_metrics", {})
        self.requirements.non_goals = data.get("non_goals", [])
        self.requirements.open_questions = data.get("open_questions", [])

        logger.info(
            "LLM analysis complete for concept '%s': %d capabilities, %d questions",
            concept[:60],
            len(self.requirements.capabilities),
            len(self.requirements.open_questions),
        )
        return self.requirements

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
