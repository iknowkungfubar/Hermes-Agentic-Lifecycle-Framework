"""HALF — Reversibility Gate: Risk-Based Task Classification.

Tasks are classified by risk level. High-reversibility tasks (UI tweaks, docs)
merge with minimal review. Low-reversibility tasks (auth logic, data migration,
payment processing) require hard human-in-the-loop (HitL) approval.

Based on the HALF doctrine's Phase 4 'Reversibility Gate' specification.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("half.reversibility_gate")


class ReversibilityLevel(enum.Enum):
    """How reversible is a change? Higher = more dangerous."""

    HIGH = "high"  # UI tweaks, docs, comments — merge with minimal review
    MEDIUM = "medium"  # New features, refactoring — require standard review
    LOW = "low"  # Auth, data migration, payments — require hard HitL approval
    CRITICAL = (
        "critical"  # Security patches, DB schema changes — require multi-party sign-off
    )


GATE_THRESHOLDS = {
    ReversibilityLevel.HIGH: {"approvals_required": 0, "human_in_loop": False},
    ReversibilityLevel.MEDIUM: {"approvals_required": 1, "human_in_loop": False},
    ReversibilityLevel.LOW: {"approvals_required": 1, "human_in_loop": True},
    ReversibilityLevel.CRITICAL: {"approvals_required": 2, "human_in_loop": True},
}


# Keywords that indicate reversibility level based on file paths and descriptions
CLASSIFICATION_KEYWORDS = {
    ReversibilityLevel.HIGH: [
        "readme",
        "docs",
        "comment",
        "typo",
        "format",
        "style",
        "css",
        "html",
        "markdown",
        ".md",
        "rename",
        "cosmetic",
        "ui",
        "display",
        "label",
    ],
    ReversibilityLevel.MEDIUM: [
        "refactor",
        "feature",
        "add",
        "update",
        "improve",
        "optimize",
        "test",
        "coverage",
        "logging",
        "metric",
        "endpoint",
    ],
    ReversibilityLevel.LOW: [
        "auth",
        "login",
        "password",
        "credential",
        "token",
        "session",
        "migration",
        "database",
        "schema",
        "index",
        "constraint",
        "api_key",
        "secret",
        "encrypt",
        "decrypt",
        "permission",
        "role",
        "admin",
        "sudo",
        "root",
        "payment",
        "billing",
    ],
    ReversibilityLevel.CRITICAL: [
        "cve",
        "security",
        "vulnerability",
        "exploit",
        "backdoor",
        "data_loss",
        "delete",
        "drop table",
        "truncate",
        "ssl",
        "certificate",
        "firewall",
        "pci",
        "hipaa",
        "gdpr",
        "rollback",
        "downgrade",
        "force",
    ],
}


@dataclass
class ReversibilityDecision:
    """Result of classifying a task's reversibility."""

    task_id: str
    task_description: str
    level: ReversibilityLevel
    confidence: float
    approvals_required: int
    requires_human: bool
    reasoning: str = ""
    affected_files: list[str] = field(default_factory=list)


class ReversibilityGate:
    """Classifies tasks by risk and determines merge approval requirements.

    Usage:
        gate = ReversibilityGate()
        decision = gate.classify("T-042", "Add OAuth2 authentication to login endpoint")
        if decision.requires_human:
            print(f"Task {decision.task_id} needs human approval ({decision.level.value})")
    """

    def __init__(self) -> None:
        self._decisions: list[ReversibilityDecision] = []

    def classify(
        self,
        task_id: str,
        description: str,
        affected_files: list[str] | None = None,
    ) -> ReversibilityDecision:
        """Classify a task by reversibility risk.

        Args:
            task_id: Task identifier.
            description: Task description.
            affected_files: Files that would be modified.

        Returns:
            ReversibilityDecision with level and approval requirements.
        """
        text = (description + " " + " ".join(affected_files or [])).lower()

        # Score each level
        scores: dict[ReversibilityLevel, int] = dict.fromkeys(ReversibilityLevel, 0)
        matched_keywords: dict[ReversibilityLevel, list[str]] = {
            level: [] for level in ReversibilityLevel
        }

        for level, keywords in CLASSIFICATION_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    scores[level] += 1
                    matched_keywords[level].append(kw)

        # Highest scoring level wins, with CRITICAL having veto power
        if scores[ReversibilityLevel.CRITICAL] > 0:
            level = ReversibilityLevel.CRITICAL
        elif scores[ReversibilityLevel.LOW] > scores.get(ReversibilityLevel.HIGH, 0):
            level = ReversibilityLevel.LOW
        elif scores[ReversibilityLevel.MEDIUM] > 0:
            level = ReversibilityLevel.MEDIUM
        elif scores[ReversibilityLevel.HIGH] > 0:
            level = ReversibilityLevel.HIGH
        else:
            level = ReversibilityLevel.MEDIUM  # Default to medium

        # Calculate confidence based on keyword match strength
        total_keywords = sum(len(kws) for kws in matched_keywords.values())
        confidence = min(1.0, total_keywords / 5)

        thresholds = GATE_THRESHOLDS[level]
        reasoning_parts = []
        if matched_keywords[level]:
            reasoning_parts.append(
                f"Matched {len(matched_keywords[level])} keywords for {level.value}: "
                f"{', '.join(matched_keywords[level][:5])}"
            )
        if total_keywords == 0:
            reasoning_parts.append(
                "No specific keywords matched — defaulting to medium"
            )

        decision = ReversibilityDecision(
            task_id=task_id,
            task_description=description,
            level=level,
            confidence=confidence,
            approvals_required=thresholds["approvals_required"],
            requires_human=bool(thresholds["human_in_loop"]),
            reasoning="; ".join(reasoning_parts),
            affected_files=affected_files or [],
        )
        self._decisions.append(decision)
        logger.info(
            "Reversibility Gate: %s → %s (human=%s, approvals=%d)",
            task_id,
            level.value,
            decision.requires_human,
            decision.approvals_required,
        )
        return decision

    def check_approval(
        self,
        task_id: str,
        approvals_received: int = 0,
        human_approved: bool = False,
    ) -> dict[str, Any]:
        """Check if a task can be merged based on approvals received.

        Args:
            task_id: Task identifier.
            approvals_received: Number of approvals received.
            human_approved: Whether a human has explicitly approved.

        Returns:
            Dict with approved, reason, and required thresholds.
        """
        decision = next((d for d in self._decisions if d.task_id == task_id), None)
        if not decision:
            return {"approved": False, "reason": f"Task {task_id} not classified"}

        if decision.requires_human and not human_approved:
            return {
                "approved": False,
                "reason": f"Task is {decision.level.value} reversibility — human-in-the-loop approval required",
                "level": decision.level.value,
                "approvals_required": decision.approvals_required,
                "approvals_received": approvals_received,
                "human_approved": human_approved,
            }

        if approvals_received < decision.approvals_required:
            return {
                "approved": False,
                "reason": f"Need {decision.approvals_required} approvals, have {approvals_received}",
                "level": decision.level.value,
                "approvals_required": decision.approvals_required,
                "approvals_received": approvals_received,
                "human_approved": human_approved,
            }

        return {
            "approved": True,
            "reason": f"All checks passed for {decision.level.value} reversibility task",
            "level": decision.level.value,
            "approvals_required": decision.approvals_required,
            "approvals_received": approvals_received,
            "human_approved": human_approved,
        }

    def get_pending_approvals(self) -> list[ReversibilityDecision]:
        """Get all decisions that need human approval.

        Returns:
            List of decisions requiring human-in-the-loop.
        """
        return [d for d in self._decisions if d.requires_human]
