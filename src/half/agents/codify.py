"""
HALF-Codify Agent (Phase 5C)

The Codification Imperative — converts manual corrections into
durable improvements to the agent system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CodificationTarget(Enum):
    AGENTS_MD = "agents_md"
    SKILL = "skill"
    HALF_WORKFLOW = "half_workflow"
    TEST_CASE = "test_case"


@dataclass
class Correction:
    """A human correction or override of an agent action."""

    id: str
    what_was_done: str
    what_was_wrong: str
    root_cause: str
    how_to_prevent: str
    target: CodificationTarget
    applied: bool = False


def analyze_correction(
    correction_id: str,
    what_was_done: str,
    what_was_wrong: str,
    root_cause: str,
    how_to_prevent: str,
) -> Correction:
    """Create a structured correction analysis.

    Determines the best codification target based on root cause.

    Args:
        correction_id: Unique identifier.
        what_was_done: What the agent did.
        what_was_wrong: What was wrong with it.
        root_cause: Why the agent made the wrong decision.
        how_to_prevent: How to avoid this next time.

    Returns:
        A Correction with appropriate target.
    """
    text = (root_cause + " " + how_to_prevent).lower()

    if any(
        kw in text for kw in ["context", "convention", "style", "naming", "pattern"]
    ):
        target = CodificationTarget.AGENTS_MD
    elif any(kw in text for kw in ["rule", "process", "workflow", "step"]):
        target = CodificationTarget.HALF_WORKFLOW
    elif any(kw in text for kw in ["test", "assert", "coverage"]):
        target = CodificationTarget.TEST_CASE
    else:
        target = CodificationTarget.SKILL

    return Correction(
        id=correction_id,
        what_was_done=what_was_done,
        what_was_wrong=what_was_wrong,
        root_cause=root_cause,
        how_to_prevent=how_to_prevent,
        target=target,
    )


class CodifyAgent:
    """Phase 5C: The Codification Imperative.

    Transforms human corrections into durable system improvements:
    - AGENTS.md updates for project-specific context
    - Skill creation/updates for general patterns
    - HALF workflow updates for lifecycle process issues
    - New test cases for correctness issues
    """

    def __init__(self) -> None:
        self.corrections: list[Correction] = []

    def register_correction(self, correction: Correction) -> None:
        """Register a human correction for codification tracking."""
        self.corrections.append(correction)

    def generate_agents_md_update(self, correction: Correction) -> str:
        """Generate an AGENTS.md update snippet from a correction.

        Args:
            correction: The analyzed correction.

        Returns:
            Markdown snippet to add to AGENTS.md.
        """
        return f"""\
### Rule: {correction.what_was_wrong}

**Source:** Correction {correction.id}

**Context:** {correction.root_cause}

**Required action:** {correction.how_to_prevent}
"""

    def generate_skill_update(self, correction: Correction) -> dict[str, str]:
        """Generate a skill update from a correction.

        Returns:
            Dict with skill name and content.
        """
        return {
            "name": f"half-{correction.target.value}",
            "content": f"""\
# {correction.id}: {correction.what_was_wrong}

## Context
{correction.root_cause}

## Correction
{correction.how_to_prevent}

## Source
Human override during: {correction.what_was_done}
""",
        }

    def generate_test_case(self, correction: Correction) -> str:
        """Generate a test case from a correction.

        Args:
            correction: The analyzed correction.

        Returns:
            Test function content.
        """
        test_name = f"test_{correction.id.lower().replace('-', '_')}"
        return f'''"""
Test: {correction.what_was_wrong}
Source: Human correction {correction.id}
"""

import pytest


def {test_name}():
    """Regression test for {correction.what_was_wrong}."""
    # Reproduce the issue
    # TODO: Implement based on: {correction.root_cause}
    assert True  # Replace with actual assertion
'''

    def get_codification_rate(self) -> float:
        """Calculate the codification rate.

        Returns:
            Percentage of corrections that resulted in durable improvements.
        """
        if not self.corrections:
            return 100.0
        applied = sum(1 for c in self.corrections if c.applied)
        return (applied / len(self.corrections)) * 100

    def render_codification_report(self) -> str:
        """Render the codification status report."""
        lines = [
            "# Codification Imperative Report",
            "",
            f"**Rate:** {self.get_codification_rate():.0f}% of corrections codified",
            "",
            "| ID | Issue | Root Cause | Target | Applied |",
            "|----|-------|------------|--------|---------|",
        ]
        for c in self.corrections:
            lines.append(
                f"| {c.id} | {c.what_was_wrong[:50]}... | "
                f"{c.root_cause[:40]}... | {c.target.value} | "
                f"{'✓' if c.applied else '✗'} |"
            )
        return "\n".join(lines)
