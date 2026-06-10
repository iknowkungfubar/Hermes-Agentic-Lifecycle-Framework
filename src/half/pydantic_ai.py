"""HALF — Pydantic AI Schema Generator.

Generates type-safe Pydantic schemas for specification documents,
API contracts, data models, and ADRs.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("half.pydantic_ai")


class Capability(BaseModel):
    """A single system capability from requirements discovery."""

    id: str = Field(pattern=r"^C-\d{3}$")
    description: str = Field(min_length=10)
    priority: str = Field(pattern=r"^P[012]$")
    confidence: str = Field(pattern=r"^(HIGH|MEDIUM|LOW)$")


class RequirementDocument(BaseModel):
    """Complete requirements document."""

    project_name: str = Field(min_length=1)
    elevator_pitch: str = Field(min_length=10)
    capabilities: list[Capability] = Field(default_factory=list)
    constraints: dict[str, str] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class FunctionRequirement(BaseModel):
    """A functional requirement with acceptance criteria."""

    id: str = Field(pattern=r"^FR-\d{3}$")
    name: str = Field(min_length=3)
    priority: str = Field(pattern=r"^P[012]$")
    description: str = Field(min_length=10)
    acceptance_criteria: list[str] = Field(min_length=1)
    files_to_create: list[str] = Field(default_factory=list)


class APIContractModel(BaseModel):
    """An API endpoint contract."""

    method: str = Field(pattern=r"^(GET|POST|PUT|PATCH|DELETE)$")
    path: str = Field(min_length=1, pattern=r"^/")
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    error_codes: list[dict[str, str]] = Field(default_factory=list)


class ArchitectureDecision(BaseModel):
    """An Architecture Decision Record."""

    id: str = Field(pattern=r"^ADR-\d{3}$")
    title: str = Field(min_length=5)
    context: str = Field(min_length=20)
    options: list[str] = Field(min_length=2)
    decision: str = Field(min_length=5)
    status: str = Field(default="Proposed", pattern=r"^(Proposed|Accepted|Deprecated)$")


class SpecificationDocument(BaseModel):
    """Complete technical specification with validation."""

    project_name: str
    functional_requirements: list[FunctionRequirement] = Field(default_factory=list)
    api_contracts: list[APIContractModel] = Field(default_factory=list)
    architecture_decisions: list[ArchitectureDecision] = Field(default_factory=list)

    @field_validator("functional_requirements")
    @classmethod
    def check_unique_fr_ids(cls, v: list[FunctionRequirement]) -> list[FunctionRequirement]:
        ids = [fr.id for fr in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate FR-IDs found")
        return v

    @field_validator("api_contracts")
    @classmethod
    def check_unique_paths(cls, v: list[APIContractModel]) -> list[APIContractModel]:
        paths = [(c.method, c.path) for c in v]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate API endpoints found")
        return v


class SchemaGenerator:
    """Generate type-safe pydantic schemas for HALF documents."""

    @staticmethod
    def generate_requirements_schema(project: str, capabilities: list[dict[str, str]]) -> RequirementDocument:
        """Generate a validated requirements document.

        Args:
            project: Project name.
            capabilities: List of capability dicts with description, priority, confidence.

        Returns:
            Validated RequirementDocument.
        """
        caps = []
        for i, cap in enumerate(capabilities):
            caps.append(Capability(
                id=f"C-{i+1:03d}",
                description=cap.get("description", ""),
                priority=cap.get("priority", "P1"),
                confidence=cap.get("confidence", "MEDIUM"),
            ))
        doc = RequirementDocument(project_name=project, elevator_pitch="", capabilities=caps)
        return doc

    @staticmethod
    def generate_specification(project: str, frs: list[dict[str, Any]]) -> SpecificationDocument:
        """Generate a validated specification document.

        Args:
            project: Project name.
            frs: List of functional requirement dicts.

        Returns:
            Validated SpecificationDocument.
        """
        reqs = []
        for i, fr in enumerate(frs):
            reqs.append(FunctionRequirement(
                id=f"FR-{i+1:03d}",
                name=fr.get("name", ""),
                priority=fr.get("priority", "P1"),
                description=fr.get("description", ""),
                acceptance_criteria=fr.get("acceptance_criteria", []),
            ))
        return SpecificationDocument(project_name=project, functional_requirements=reqs)
