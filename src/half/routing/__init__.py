"""HALF — Task-to-Workflow Routing Engine.

Dynamically routes business objectives to appropriate workflows based
on semantic intent analysis.

Split from a single 478-line module into a package organized by concern.
All symbols are re-exported here for backward compatibility.
"""

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
from half.routing.router import TaskRouter

__all__ = [
    "TaskDomain",
    "WorkflowType",
    "CODE_KEYWORDS",
    "CONTENT_KEYWORDS",
    "DATA_KEYWORDS",
    "FINANCIAL_KEYWORDS",
    "LEGAL_KEYWORDS",
    "MEDIA_KEYWORDS",
    "RESEARCH_KEYWORDS",
    "LoopScript",
    "LoopScriptTask",
    "RoutingDecision",
    "TaskRouter",
]
