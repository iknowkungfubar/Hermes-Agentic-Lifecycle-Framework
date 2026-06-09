"""
HALF-Iterate Agent (Phase 5B)

Issue tracking, triage workflow, and quality-of-life updates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IssueType(Enum):
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    TECHNICAL_DEBT = "technical-debt"
    INCIDENT = "incident"


@dataclass
class Issue:
    """A tracked issue."""

    id: str
    title: str
    issue_type: IssueType
    description: str
    severity: str = "medium"  # low, medium, high, critical
    estimated_hours: float = 0.0
    status: str = "open"  # open, triaged, in-progress, resolved
    created_at: str = ""
    resolved_at: str = ""


@dataclass
class TriageResult:
    """Result of triaging an issue."""

    issue_id: str
    assigned_action: str
    auto_fixable: bool = False
    requires_human: bool = False
    pr_created: bool = False
    reasoning: str = ""


# ─── Issue Classifier ─────────────────────────────────────────────────────────


def classify_input(
    title: str,
    description: str,
) -> IssueType:
    """Classify an input into an issue type based on keywords."""
    text = f"{title} {description}".lower()

    if any(
        kw in text for kw in ["crash", "error", "broken", "fail", "bug", "regression"]
    ):
        return IssueType.BUG
    if any(
        kw in text for kw in ["feature", "request", "could we", "would be nice", "add"]
    ):
        return IssueType.FEATURE
    if any(
        kw in text
        for kw in ["refactor", "clean", "tech debt", "technical debt", "legacy"]
    ):
        return IssueType.TECHNICAL_DEBT
    if any(kw in text for kw in ["outage", "down", "incident", "p1", "p0"]):
        return IssueType.INCIDENT

    return IssueType.IMPROVEMENT


def estimate_size(issue: Issue) -> str:
    """Estimate the size of an issue."""
    if issue.estimated_hours <= 0:
        return "unknown"
    if issue.estimated_hours < 1:
        return "small"
    if issue.estimated_hours < 4:
        return "medium"
    return "large"


# ─── Iterate Agent ────────────────────────────────────────────────────────────


class IterateAgent:
    """Phase 5B: Issue tracking and triage workflow."""

    def __init__(self) -> None:
        self.issues: list[Issue] = []
        self.triage_results: list[TriageResult] = []

    def create_issue(
        self,
        title: str,
        description: str,
        issue_type: IssueType | None = None,
        severity: str = "medium",
    ) -> Issue:
        """Create and classify a new issue.

        Args:
            title: Issue title.
            description: Issue description.
            issue_type: Optional type override. Auto-classified if not provided.
            severity: Issue severity.

        Returns:
            The created Issue.
        """
        if issue_type is None:
            issue_type = classify_input(title, description)

        issue_id = f"I-{len(self.issues) + 1:04d}"
        import datetime

        issue = Issue(
            id=issue_id,
            title=title,
            issue_type=issue_type,
            description=description,
            severity=severity,
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        self.issues.append(issue)
        return issue

    def triage(self, issue_id: str) -> TriageResult:
        """Triage an issue — determine action and auto-fixability.

        Args:
            issue_id: Issue to triage.

        Returns:
            TriageResult with action recommendation.
        """
        issue = next((i for i in self.issues if i.id == issue_id), None)
        if not issue:
            msg = f"Issue not found: {issue_id}"
            raise ValueError(msg)

        # Determine if auto-fixable
        auto_fixable = (
            issue.issue_type == IssueType.BUG and issue.severity != "critical"
        )
        requires_human = (
            issue.issue_type == IssueType.INCIDENT
            or issue.severity == "critical"
            or issue.estimated_hours > 4
        )

        # Determine action
        if issue.issue_type == IssueType.BUG:
            action = "Reproduce -> root cause -> fix (TDD) -> PR"
        elif issue.issue_type == IssueType.FEATURE:
            action = "Create mini-spec -> estimate -> implement"
        elif issue.issue_type == IssueType.TECHNICAL_DEBT:
            action = "Document debt -> estimate fix cost -> prioritize"
        else:
            action = "Analyze -> determine action -> execute"

        result = TriageResult(
            issue_id=issue_id,
            assigned_action=action,
            auto_fixable=auto_fixable,
            requires_human=requires_human,
            reasoning=(
                f"Classified as {issue.issue_type.value}. "
                f"Size: {estimate_size(issue)}. "
                f"{'Auto-fixable.' if auto_fixable else 'Requires human review.'}"
            ),
        )
        self.triage_results.append(result)
        issue.status = "triaged"
        return result

    def get_open_issues(self) -> list[Issue]:
        """Get all open issues."""
        return [i for i in self.issues if i.status != "resolved"]

    def render_triage_playbook(self) -> str:
        """Render the issue triage playbook."""
        return """\
# Issue Triage Playbook

## Classification

| Keyword | Type |
|---------|------|
| crash, error, broken, fail, bug, regression | Bug |
| feature, request, "could we", "would be nice" | Feature |
| refactor, clean, tech debt, legacy | Technical Debt |
| outage, down, incident | Incident |
| Everything else | Improvement |

## Triage Flow

```
INPUT → Classify → Estimate → Auto-fix? → Execute
                                   ↓
                              Requires Human?
                                   ↓
                            Queue for review
```

## Bug Workflow
1. **Reproduce:** Create a failing test that demonstrates the bug
2. **Root cause:** Analyze logs, stack traces, and code
3. **Fix:** Implement the fix (TDD — test first, then code)
4. **Verify:** Test passes, existing tests still pass
5. **PR:** One-commit PR, reference the issue ID

## Feature Workflow
1. **Mini-spec:** Follow Phase 1 pattern at reduced scope
2. **Estimate:** Small (<1h), Medium (1-4h), Large (>4h)
3. **If large:** Break into smaller tasks
4. **Implement:** Per Phase 2 pattern (skip full phase gates)

## Technical Debt Workflow
1. **Document:** What, where, why it's a problem
2. **Estimate:** Cost to fix vs cost to leave
3. **Prioritize:** HIGH (blocker), MEDIUM (velocity drag), LOW (cosmetic)
4. **Fix HIGH** items in current iteration
5. **Queue** MEDIUM/LOW for backlog
"""
