"""HALF — Agent Skills Module.

All 16 agent skills that execute the 5-phase SDLC pipeline.
"""

from __future__ import annotations

from src.agents.architect import ArchitectAgent
from src.agents.cicd import CICDAgent
from src.agents.codify import CodifyAgent
from src.agents.discovery import DiscoveryAgent
from src.agents.implement import ImplementAgent
from src.agents.infrastructure import InfrastructureAgent
from src.agents.integration import IntegrationAgent
from src.agents.iterate import IterateAgent
from src.agents.launch import LaunchAgent
from src.agents.observe import ObserveAgent
from src.agents.scaffold import ScaffoldAgent
from src.agents.security import SecurityAgent
from src.agents.specification import SpecificationAgent
from src.agents.testing import TestingAgent

from src.agents.code_simplifier import CodeSimplifier

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
