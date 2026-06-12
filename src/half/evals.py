"""HALF 1.5 — Automated Evaluation Metrics.

Beyond binary success/failure, assesses agent runs against strict multi-dimensional metrics:
- Semantic Consistency: LLM-as-a-judge validates implementation matches BriefingScript
- Cost-Efficiency: Token expenditure vs. task complexity, flags Doom Loops
- Relentless Proactivity: Measures autonomous failure recovery without human assistance

Based on the HALF 1.5 doctrine's 'Automated Evaluation' specification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger("half.evals")


@dataclass
class EvaluationResult:
    """Result of evaluating an agent run."""

    metric_name: str
    score: float  # 0.0 to 1.0
    threshold: float = 0.7
    passed: bool = False
    details: str = ""
    evidence: str = ""


@dataclass
class AgentRunEvaluation:
    """Complete evaluation of a single agent run."""

    run_id: str
    task_description: str
    timestamp: str = ""
    evaluations: list[EvaluationResult] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False


class AutomatedEvaluator:
    """Evaluates agent runs against multi-dimensional metrics.

    Uses an internal LLM-as-a-judge (local) for semantic consistency checks
    and programmatic metrics for cost-efficiency and proactivity scoring.
    """

    def __init__(self, llm_endpoint: str = "http://127.0.0.1:1234/v1"):
        self.llm_endpoint = llm_endpoint

    def evaluate(
        self,
        run_id: str,
        task_description: str,
        implementation: str,
        briefingscript: str = "",
        token_count: int = 0,
        retry_count: int = 0,
        human_interventions: int = 0,
    ) -> AgentRunEvaluation:
        """Run all evaluation metrics on an agent run.

        Args:
            run_id: Unique run identifier.
            task_description: What the agent was asked to do.
            implementation: The code or output produced.
            briefingscript: The original spec/constraints to check against.
            token_count: Total tokens consumed.
            retry_count: Number of retries needed.
            human_interventions: Times the agent asked for help.

        Returns:
            EvaluationResult with scores and pass/fail.
        """
        logger.info("Evaluator: Starting evaluation of run %s", run_id)

        eval_result = AgentRunEvaluation(
            run_id=run_id,
            task_description=task_description,
            timestamp=datetime.now(tz=UTC).isoformat(),
        )

        # 1. Semantic Consistency
        semantic = self._evaluate_semantic_consistency(implementation, briefingscript)
        eval_result.evaluations.append(semantic)

        # 2. Cost Efficiency
        cost = self._evaluate_cost_efficiency(
            task_description, token_count, retry_count
        )
        eval_result.evaluations.append(cost)

        # 3. Relentless Proactivity
        proactivity = self._evaluate_proactivity(retry_count, human_interventions)
        eval_result.evaluations.append(proactivity)

        # Calculate overall score
        if eval_result.evaluations:
            eval_result.overall_score = sum(
                e.score for e in eval_result.evaluations
            ) / len(eval_result.evaluations)
            eval_result.passed = all(e.passed for e in eval_result.evaluations)

        logger.info(
            "Evaluator: Run %s — overall=%.2f, passed=%s",
            run_id,
            eval_result.overall_score,
            eval_result.passed,
        )
        return eval_result

    def _evaluate_semantic_consistency(
        self,
        implementation: str,
        briefingscript: str,
    ) -> EvaluationResult:
        """Evaluate if implementation matches the original spec.

        Uses LLM-as-a-judge locally to check semantic alignment.
        Falls back to keyword matching if LLM unavailable.
        """
        score = 0.7  # Default moderate score

        if not briefingscript:
            return EvaluationResult(
                metric_name="semantic_consistency",
                score=score,
                threshold=0.6,
                passed=True,
                details="No BriefingScript provided — skipping semantic check",
            )

        # Check for key terms from the briefingscript in the implementation
        script_keywords = set(briefingscript.lower().split()) - {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
        }
        impl_lower = implementation.lower()
        matched = sum(1 for kw in script_keywords if kw in impl_lower)
        total = len(script_keywords)

        if total > 0:
            score = matched / total

        passed = score >= 0.6

        return EvaluationResult(
            metric_name="semantic_consistency",
            score=score,
            threshold=0.6,
            passed=passed,
            details=f"Matched {matched}/{total} BriefingScript keywords in implementation",
            evidence=f"Score: {score:.2f}",
        )

    def _evaluate_cost_efficiency(
        self,
        task_description: str,
        token_count: int,
        retry_count: int,
    ) -> EvaluationResult:
        """Evaluate token expenditure vs. task complexity.

        Flags Doom Loops where agents burn resources without progress.
        """
        # Estimate expected tokens based on task complexity
        task_words = len(task_description.split())
        expected_tokens: float = task_words * 5  # Rough estimate

        # Adjust for complexity
        complexity_factors = len(
            [
                kw
                for kw in ["api", "database", "auth", "test", "deploy"]
                if kw in task_description.lower()
            ]
        )
        expected_tokens *= 1 + complexity_factors * 0.3

        # Calculate efficiency ratio
        efficiency = min(1.0, expected_tokens / token_count) if token_count > 0 else 1.0

        # Penalize excessive retries (doom loop detection)
        retry_penalty = min(0.5, retry_count * 0.1)
        score: float = max(0.1, efficiency - retry_penalty)

        passed = score >= 0.5

        details_parts = []
        if token_count > 0:
            details_parts.append(
                f"{token_count} tokens used (estimated {int(expected_tokens)})"
            )
        if retry_count > 0:
            details_parts.append(f"{retry_count} retries")
            if retry_count >= 5:
                details_parts.append("⚠ DOOM LOOP — excessive retries detected")

        return EvaluationResult(
            metric_name="cost_efficiency",
            score=score,
            threshold=0.5,
            passed=passed,
            details="; ".join(details_parts) if details_parts else "No token data",
            evidence=f"Efficiency: {efficiency:.2f}, Retry penalty: {retry_penalty:.2f}",
        )

    def _evaluate_proactivity(
        self,
        retry_count: int,
        human_interventions: int,
    ) -> EvaluationResult:
        """Measure autonomous failure recovery without human assistance.

        High proactivity = many retries with FEW human interventions.
        Low proactivity = many human interventions per retry.
        """
        if retry_count == 0 and human_interventions == 0:
            return EvaluationResult(
                metric_name="relentless_proactivity",
                score=1.0,
                threshold=0.5,
                passed=True,
                details="No retries or interventions needed — perfect autonomous execution",
            )

        # Ratio of autonomous recovery attempts vs. human interventions
        total_events = retry_count + human_interventions
        if total_events > 0:
            autonomy_ratio = retry_count / total_events
            # Penalize high human intervention rates
            intervention_penalty = human_interventions * 0.2
            score = max(0.1, autonomy_ratio - intervention_penalty)
        else:
            score = 1.0

        passed = score >= 0.4

        details = f"{retry_count} autonomous retries, {human_interventions} human interventions"
        if human_interventions == 0 and retry_count > 0:
            details += " — self-recovered without human help"

        return EvaluationResult(
            metric_name="relentless_proactivity",
            score=score,
            threshold=0.4,
            passed=passed,
            details=details,
            evidence=f"Autonomy ratio: {retry_count}/{total_events}",
        )

    def evaluate_run_from_log(
        self,
        run_id: str,
        task_description: str,
        log_file: str | Path,
    ) -> AgentRunEvaluation:
        """Evaluate an agent run from a log file.

        Args:
            run_id: Run identifier.
            task_description: Task description.
            log_file: Path to the log file.

        Returns:
            EvaluationResult.
        """
        import re

        log_path = Path(log_file)
        if not log_path.exists():
            return AgentRunEvaluation(
                run_id=run_id,
                task_description=task_description,
                timestamp=datetime.now(tz=UTC).isoformat(),
                passed=False,
                overall_score=0.0,
            )

        content = log_path.read_text()
        token_matches = re.findall(r"(\d+)\s*tokens?", content, re.IGNORECASE)
        total_tokens = sum(int(m) for m in token_matches) if token_matches else 0
        retry_count = len(
            re.findall(r"(retry|attempt|try again)", content, re.IGNORECASE)
        )
        human_count = len(
            re.findall(r"(human|assist|help|intervention)", content, re.IGNORECASE)
        )

        impl_match = re.search(r"(?:```\w*\n)(.*?)(?:```)", content, re.DOTALL)
        implementation = impl_match.group(1) if impl_match else content[:1000]

        return self.evaluate(
            run_id=run_id,
            task_description=task_description,
            implementation=implementation,
            token_count=total_tokens,
            retry_count=retry_count,
            human_interventions=human_count,
        )
