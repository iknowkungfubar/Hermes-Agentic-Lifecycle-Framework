"""HALF — Routing enums for Task-to-Workflow Routing Engine."""

from __future__ import annotations

import enum


class TaskDomain(enum.Enum):
    """Domain categories for task routing."""

    SOFTWARE_ENGINEERING = "software_engineering"
    MARKET_RESEARCH = "market_research"
    DATA_ANALYSIS = "data_analysis"
    MEDIA_SYNTHESIS = "media_synthesis"
    LEGAL_DOCUMENT = "legal_document"
    FINANCIAL_ANALYSIS = "financial_analysis"
    CONTENT_WRITING = "content_writing"
    GENERAL = "general"


class WorkflowType(enum.Enum):
    """Workflow types that tasks can be routed to."""

    TRI_PHASIC = "tri_phasic"  # Research -> Plan -> Implement
    RESEARCH_ONLY = "research_only"  # Read-only analysis
    DATA_PIPELINE = "data_pipeline"  # Extract -> Transform -> Load
    CONTENT_GENERATION = "content_generation"  # Research -> Outline -> Write -> Review
    CUSTOM_DAG = "custom_dag"  # Dynamically constructed DAG
