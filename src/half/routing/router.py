"""HALF — Task-to-Workflow Routing Engine.

Dynamically routes business objectives to appropriate workflows based
on semantic intent analysis. Code tasks go to the Tri-Phasic Execution Loop.
Non-code tasks (research, data analysis, media synthesis) get custom
heterogeneous DAG LoopScripts via the Agent Communication Protocol.

Based on the HALF doctrine's 'Universal Agentic Engine' specification.
"""

from __future__ import annotations

import json
import logging

from half.routing.enums import TaskDomain, WorkflowType
from half.routing.keywords import (
    CODE_KEYWORDS,
    CONTENT_KEYWORDS,
    DATA_KEYWORDS,
    FINANCIAL_KEYWORDS,
    LEGAL_KEYWORDS,
    MEDIA_KEYWORDS,
    RESEARCH_KEYWORDS,
)
from half.routing.models import LoopScript, LoopScriptTask, RoutingDecision

logger = logging.getLogger("half.routing")


class TaskRouter:
    """Routes business objectives to appropriate workflows.

    Analyzes the intent of a task description and routes it to the
    appropriate workflow type. For code tasks, uses the Tri-Phasic Loop.
    For other domains, constructs custom DAG LoopScripts.
    """

    def __init__(self) -> None:
        self._keyword_map: list[tuple[list[str], TaskDomain, WorkflowType, float]] = [
            (
                CODE_KEYWORDS,
                TaskDomain.SOFTWARE_ENGINEERING,
                WorkflowType.TRI_PHASIC,
                0.9,
            ),
            (
                RESEARCH_KEYWORDS,
                TaskDomain.MARKET_RESEARCH,
                WorkflowType.RESEARCH_ONLY,
                0.8,
            ),
            (DATA_KEYWORDS, TaskDomain.DATA_ANALYSIS, WorkflowType.DATA_PIPELINE, 0.8),
            (
                CONTENT_KEYWORDS,
                TaskDomain.CONTENT_WRITING,
                WorkflowType.CONTENT_GENERATION,
                0.8,
            ),
            (
                FINANCIAL_KEYWORDS,
                TaskDomain.FINANCIAL_ANALYSIS,
                WorkflowType.DATA_PIPELINE,
                0.7,
            ),
            (MEDIA_KEYWORDS, TaskDomain.MEDIA_SYNTHESIS, WorkflowType.CUSTOM_DAG, 0.7),
            (
                LEGAL_KEYWORDS,
                TaskDomain.LEGAL_DOCUMENT,
                WorkflowType.CONTENT_GENERATION,
                0.7,
            ),
        ]

    def route(self, task_description: str) -> RoutingDecision:
        """Route a task description to the appropriate workflow.

        Args:
            task_description: Natural language description of the task.

        Returns:
            RoutingDecision with domain, workflow, and confidence.
        """
        text = task_description.lower()

        best_match: tuple[TaskDomain, WorkflowType, float, str] = (
            TaskDomain.GENERAL,
            WorkflowType.CUSTOM_DAG,
            0.3,
            "No specific keywords matched",
        )

        for keywords, domain, workflow, base_conf in self._keyword_map:
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                confidence = min(1.0, base_conf + (matches * 0.05))
                if confidence > best_match[2]:
                    best_match = (
                        domain,
                        workflow,
                        confidence,
                        f"{matches} keyword matches for {domain.value}",
                    )

        domain, workflow, confidence, reasoning = best_match
        psm_hints = self._infer_psm_hints(domain, text)

        return RoutingDecision(
            task_description=task_description,
            domain=domain,
            workflow=workflow,
            confidence=confidence,
            requires_psm=len(psm_hints) > 0,
            psm_hints=psm_hints,
            reasoning=reasoning,
        )

    def _infer_psm_hints(self, domain: TaskDomain, text: str) -> list[str]:
        """Infer what Portable Skill Modules might be needed."""
        hints: list[str] = []
        if "web" in text or "scrape" in text or "browser" in text:
            hints.append("browser-use")
        if "stock" in text or "market" in text or "financial" in text:
            hints.append("financial-data")
        if "legal" in text or "contract" in text or "compliance" in text:
            hints.append("legal-document-generation")
        if "image" in text or "media" in text:
            hints.append("media-synthesis")
        if "data" in text or "csv" in text or "excel" in text:
            hints.append("data-analysis-pandas")
        return hints

    def build_loopscript(self, decision: RoutingDecision) -> LoopScript:
        """Build a LoopScript DAG for the routed workflow.

        Args:
            decision: The routing decision from route().

        Returns:
            A LoopScript with tasks in DAG order.
        """
        if decision.workflow == WorkflowType.TRI_PHASIC:
            return self._build_tri_phasic(decision)
        if decision.workflow == WorkflowType.RESEARCH_ONLY:
            return self._build_research(decision)
        if decision.workflow == WorkflowType.DATA_PIPELINE:
            return self._build_data_pipeline(decision)
        if decision.workflow == WorkflowType.CONTENT_GENERATION:
            return self._build_content(decision)
        return self._build_custom_dag(decision)

    def _build_tri_phasic(self, decision: RoutingDecision) -> LoopScript:
        return LoopScript(
            phases=[
                LoopScriptTask(
                    "research",
                    "Codebase Analysis",
                    "HALF-Research",
                    "read-only",
                    outputs=["codebase-analysis.md"],
                ),
                LoopScriptTask(
                    "plan",
                    "Implementation Plan",
                    "HALF-Plan",
                    "design-only",
                    inputs=["codebase-analysis.md"],
                    outputs=["implementation-spec.md"],
                ),
                LoopScriptTask(
                    "implement",
                    "Implementation",
                    "HALF-Implement",
                    "write-restricted",
                    inputs=["implementation-spec.md"],
                    outputs=["implemented-code"],
                ),
                LoopScriptTask(
                    "simplify",
                    "Code Simplification",
                    "HALF-CodeSimplifier",
                    "write-restricted",
                    inputs=["implemented-code"],
                    outputs=["simplified-code"],
                ),
            ],
            chain=["research", "plan", "implement", "simplify"],
            tri_phasic=["research", "plan", "implement"],
        )

    def _build_research(self, decision: RoutingDecision) -> LoopScript:
        return LoopScript(
            phases=[
                LoopScriptTask(
                    "collect",
                    "Data Collection",
                    "HALF-Research",
                    "read-only",
                    outputs=["raw-data.md"],
                ),
                LoopScriptTask(
                    "synthesize",
                    "Synthesis",
                    "HALF-Discovery",
                    "design-only",
                    inputs=["raw-data.md"],
                    outputs=["analysis-report.md"],
                ),
            ],
            chain=["collect", "synthesize"],
        )

    def _build_data_pipeline(self, decision: RoutingDecision) -> LoopScript:
        return LoopScript(
            phases=[
                LoopScriptTask(
                    "extract",
                    "Data Extraction",
                    "HALF-Research",
                    "read-only",
                    outputs=["extracted-data"],
                ),
                LoopScriptTask(
                    "transform",
                    "Data Transformation",
                    "HALF-Implement",
                    "write-restricted",
                    inputs=["extracted-data"],
                    outputs=["transformed-data"],
                ),
                LoopScriptTask(
                    "analyze",
                    "Analysis",
                    "HALF-Research",
                    "design-only",
                    inputs=["transformed-data"],
                    outputs=["analysis-report.md"],
                ),
            ],
            chain=["extract", "transform", "analyze"],
        )

    def _build_content(self, decision: RoutingDecision) -> LoopScript:
        return LoopScript(
            phases=[
                LoopScriptTask(
                    "outline",
                    "Content Outline",
                    "HALF-Discovery",
                    "read-only",
                    outputs=["outline.md"],
                ),
                LoopScriptTask(
                    "draft",
                    "First Draft",
                    "HALF-Implement",
                    "write-restricted",
                    inputs=["outline.md"],
                    outputs=["draft.md"],
                ),
                LoopScriptTask(
                    "review",
                    "Quality Review",
                    "HALF-Testing",
                    "design-only",
                    inputs=["draft.md"],
                    outputs=["final-content.md"],
                ),
            ],
            chain=["outline", "draft", "review"],
        )

    def _build_custom_dag(self, decision: RoutingDecision) -> LoopScript:
        return LoopScript(
            phases=[
                LoopScriptTask(
                    "define",
                    "Problem Definition",
                    "HALF-Discovery",
                    "read-only",
                    outputs=["problem-statement.md"],
                ),
                LoopScriptTask(
                    "execute",
                    "Execution",
                    "HALF-Implement",
                    "write-restricted",
                    inputs=["problem-statement.md"],
                    outputs=["results"],
                ),
                LoopScriptTask(
                    "verify",
                    "Verification",
                    "HALF-Testing",
                    "design-only",
                    inputs=["results"],
                    outputs=["verification-report.md"],
                ),
            ],
            chain=["define", "execute", "verify"],
        )

    def serialize_loopscript(self, script: LoopScript) -> str:
        """Serialize a LoopScript to YAML-like format."""
        lines = [
            "# LoopScript -- Declarative DAG SOP",
            "# Generated by HALF Task-to-Workflow Router",
            f'version: "{script.version}"',
            "phases:",
        ]
        for phase in script.phases:
            lines.extend(
                [
                    f"  - id: {phase.id}",
                    f"    agent: {phase.agent}",
                    f"    mode: {phase.mode}",
                ]
            )
            if phase.inputs:
                lines.append(f"    inputs: {json.dumps(phase.inputs)}")
            if phase.outputs:
                lines.append(f"    outputs: {json.dumps(phase.outputs)}")
            if phase.depends_on:
                lines.append(f"    depends_on: {json.dumps(phase.depends_on)}")

        lines.append(f"chain: {json.dumps(script.chain)}")
        if script.tri_phasic:
            lines.append(f"tri_phasic: {json.dumps(script.tri_phasic)}")
        return "\n".join(lines)
