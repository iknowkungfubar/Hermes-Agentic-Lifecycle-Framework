"""HALF 1.5 — Interactive Interview System + PDA Personality.

Before coding begins, the PDA conducts an interactive interview with the user
to extract missing technical constraints and refine the BriefingScript.
Supports personality customization via settings for tone, verbosity, and style.

Based on the HALF 1.5 doctrine's 'Interactive Interviews & Personality' spec.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("half.interview")


@dataclass
class PDAProfile:
    """Personality profile for the Commander Agent PDA."""

    name: str = "Hermes"
    tone: str = "professional"  # professional, casual, playful, academic
    verbosity: int = 3  # 1-5, higher = more detailed
    style: str = "direct"  # direct, conversational, socratic
    emoji_enabled: bool = True
    custom_instructions: str = ""


@dataclass
class BriefingScript:
    """The refined technical specification from the interview process."""

    project_name: str = ""
    description: str = ""
    technical_constraints: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    target_users: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    confidence_gaps: list[dict[str, str]] = field(default_factory=list)
    interview_complete: bool = False


# ─── Interview Questions by Domain ────────────────────────────────────────────

TECHNICAL_QUESTIONS = [
    {
        "id": "tech_stack",
        "question": "What tech stack should we use? (e.g., Python/FastAPI, TypeScript/Next.js, Rust/Axum)",
        "field": "tech_stack",
        "confidence_weight": 0.3,
    },
    {
        "id": "database",
        "question": "What database or storage solution does this need? (e.g., PostgreSQL, SQLite, S3, Redis)",
        "field": "technical_constraints",
        "confidence_weight": 0.4,
    },
    {
        "id": "auth",
        "question": "Does this need authentication? If so, what kind? (e.g., JWT, OAuth, API keys, none)",
        "field": "technical_constraints",
        "confidence_weight": 0.5,
    },
    {
        "id": "deployment",
        "question": "How should this be deployed? (e.g., Docker, serverless, desktop app, mobile)",
        "field": "technical_constraints",
        "confidence_weight": 0.3,
    },
    {
        "id": "scaling",
        "question": "What's the expected scale? (e.g., single user, 100 users, 10K+ concurrent)",
        "field": "success_metrics",
        "confidence_weight": 0.2,
    },
]

BUSINESS_QUESTIONS = [
    {
        "id": "core_feature",
        "question": "What's the single most important feature this must have?",
        "field": "description",
        "confidence_weight": 0.5,
    },
    {
        "id": "users",
        "question": "Who are the primary users? (e.g., developers, end-users, admins, API consumers)",
        "field": "target_users",
        "confidence_weight": 0.3,
    },
    {
        "id": "non_goals",
        "question": "Is there anything explicitly OUT of scope for this version?",
        "field": "non_goals",
        "confidence_weight": 0.2,
    },
    {
        "id": "timeline",
        "question": "What's the timeline? (e.g., ASAP prototype, 2-week sprint, production by Q3)",
        "field": "technical_constraints",
        "confidence_weight": 0.2,
    },
]


class InterviewEngine:
    """Conducts interactive interviews to extract technical constraints.

    The PDA asks targeted questions, records answers, and builds a
    BriefingScript. Questions adapt based on previous answers.
    """

    def __init__(self, profile: PDAProfile | None = None):
        self.profile = profile or PDAProfile()
        self.script = BriefingScript()
        self._question_log: list[dict[str, str]] = []

    def start_interview(
        self, project_name: str, initial_description: str
    ) -> list[dict[str, Any]]:
        """Start the interview process. Returns the first batch of questions.

        Args:
            project_name: The project name.
            initial_description: Initial project description.

        Returns:
            List of question dicts to ask the user.
        """
        self.script.project_name = project_name
        self.script.description = initial_description
        logger.info("Interview: Starting interview for '%s'", project_name)

        # Start with business questions first, then technical
        questions = BUSINESS_QUESTIONS + TECHNICAL_QUESTIONS
        return [
            {"id": str(q["id"]), "question": self._format_question(str(q["question"]))}
            for q in questions
        ]

    def process_answer(self, question_id: str, answer: str) -> dict[str, Any]:
        """Process an answer from the user.

        Args:
            question_id: The question being answered.
            answer: The user's answer.

        Returns:
            Dict with next steps and any follow-up questions.
        """
        self._question_log.append({"id": question_id, "answer": answer})

        # Find the question definition
        all_questions = BUSINESS_QUESTIONS + TECHNICAL_QUESTIONS
        q_def = next((q for q in all_questions if q["id"] == question_id), None)

        if not q_def:
            return {
                "status": "unknown_question",
                "message": f"No question found with id '{question_id}'",
            }

        field = q_def["field"]
        answer_list = [s.strip() for s in answer.split(",") if s.strip()]

        # Store in the appropriate field
        if field == "tech_stack":
            self.script.tech_stack.extend(answer_list)
        elif field == "description":
            self.script.description = answer
        elif field == "target_users":
            self.script.target_users.extend(answer_list)
        elif field == "non_goals":
            self.script.non_goals.extend(answer_list)
        elif field == "technical_constraints":
            self.script.technical_constraints.extend(answer_list)
        elif field == "success_metrics":
            self.script.success_metrics.extend(answer_list)

        # Check for confidence gaps (answers that suggest uncertainty)
        uncertainty_markers = ["not sure", "maybe", "i don't know", "unsure", "?"]
        if any(marker in answer.lower() for marker in uncertainty_markers):
            self.script.confidence_gaps.append(
                {
                    "question_id": question_id,
                    "question": str(q_def["question"]),
                    "note": "Low confidence in answer - consider further research",
                }
            )

        return {
            "status": "recorded",
            "field": field,
            "recorded_value": answer if field == "description" else answer_list,
        }

    def finalize(self) -> BriefingScript:
        """Finalize the BriefingScript after all questions are answered.

        Returns:
            The completed BriefingScript.
        """
        self.script.interview_complete = True

        # Add default values for empty fields
        if not self.script.non_goals:
            self.script.non_goals = ["TBD — will be refined during development"]

        logger.info(
            "Interview: BriefingScript finalized for '%s' (%d constraints, %d questions)",
            self.script.project_name,
            len(self.script.technical_constraints),
            len(self._question_log),
        )
        return self.script

    def get_briefingscript_markdown(self) -> str:
        """Render the BriefingScript as markdown.

        Returns:
            Markdown-formatted BriefingScript.
        """
        lines = [
            f"# BriefingScript: {self.script.project_name}",
            "",
            "## Description",
            self.script.description,
            "",
        ]
        if self.script.tech_stack:
            lines.extend(
                ["## Tech Stack", "", *[f"- {t}" for t in self.script.tech_stack], ""]
            )
        if self.script.technical_constraints:
            lines.extend(
                [
                    "## Technical Constraints",
                    "",
                    *[f"- {c}" for c in self.script.technical_constraints],
                    "",
                ]
            )
        if self.script.target_users:
            lines.extend(
                [
                    "## Target Users",
                    "",
                    *[f"- {u}" for u in self.script.target_users],
                    "",
                ]
            )
        if self.script.success_metrics:
            lines.extend(
                [
                    "## Success Metrics",
                    "",
                    *[f"- {m}" for m in self.script.success_metrics],
                    "",
                ]
            )
        if self.script.non_goals:
            lines.extend(
                ["## Non-Goals", "", *[f"- {n}" for n in self.script.non_goals], ""]
            )
        if self.script.confidence_gaps:
            lines.extend(["## Confidence Gaps", ""])
            for gap in self.script.confidence_gaps:
                lines.append(f"- {gap['question']}: {gap['note']}")
            lines.append("")

        return "\n".join(lines)

    def _format_question(self, question: str) -> str:
        """Format a question according to the PDA's personality profile.

        Args:
            question: Raw question text.

        Returns:
            Formatted question.
        """
        if self.profile.tone == "casual":
            prefixes = ["Hey! ", "Quick one: ", "Let me ask: "]
            import random

            return random.choice(prefixes) + question.lower()
        if self.profile.tone == "playful":
            return "✨ " + question.replace("?", "? 🧐")
        if self.profile.tone == "academic":
            return "Inquiry: " + question
        return question  # professional/direct

    def set_personality(self, profile: PDAProfile) -> None:
        """Update the PDA's personality profile.

        Args:
            profile: New profile settings.
        """
        self.profile = profile
        logger.info(
            "Interview: PDA personality updated — tone=%s, verbosity=%d",
            profile.tone,
            profile.verbosity,
        )

    def get_personality_prompt(self) -> str:
        """Generate a system prompt snippet for the personality.

        Returns:
            Prompt text to inject into the agent's context.
        """
        tone_desc = {
            "professional": "Maintain a professional, direct tone. Be precise and efficient.",
            "casual": "Be friendly and conversational. Use casual language.",
            "playful": "Be engaging and playful. Use emojis and creative language.",
            "academic": "Be thorough and precise. Use formal language and cite reasoning.",
        }
        base = tone_desc.get(self.profile.tone, "")
        return f"[PDA Personality: {self.profile.name}. {base} Verbosity level: {self.profile.verbosity}/5.]"
