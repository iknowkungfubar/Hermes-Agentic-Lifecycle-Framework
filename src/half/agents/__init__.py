"""HALF — Agent Skills Module.

All 16 agent skills that execute the 5-phase SDLC pipeline.
"""

from __future__ import annotations

from half.agents.architect import ArchitectAgent
from half.agents.cicd import CICDAgent
from half.agents.codify import CodifyAgent
from half.agents.discovery import DiscoveryAgent
from half.agents.implement import ImplementAgent
from half.agents.infrastructure import InfrastructureAgent
from half.agents.integration import IntegrationAgent
from half.agents.iterate import IterateAgent
from half.agents.launch import LaunchAgent
from half.agents.observe import ObserveAgent
from half.agents.scaffold import ScaffoldAgent
from half.agents.security import SecurityAgent
from half.agents.specification import SpecificationAgent
from half.agents.testing import TestingAgent

from half.agents.code_simplifier import CodeSimplifier

__all__ = [
    "ArchitectAgent",
    "CICDAgent",
    "CodeSimplifier",
    "CodifyAgent",
    "DiscoveryAgent",
    "ImplementAgent",
    "InfrastructureAgent",
    "IntegrationAgent",
    "IterateAgent",
    "LaunchAgent",
    "ObserveAgent",
    "ScaffoldAgent",
    "SecurityAgent",
    "SpecificationAgent",
    "TestingAgent",
]
