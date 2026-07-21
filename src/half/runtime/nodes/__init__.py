"""HALF LangGraph Phase Nodes.

Split from a single 754-line module into a package organized by phase.
All symbols are re-exported here for backward compatibility.
"""

from half.runtime.nodes._write_artifact import _write_artifact
from half.runtime.nodes.phase1 import (
    phase_1_architecture,
    phase_1_discovery,
    phase_1_gate,
    phase_1_specification,
)
from half.runtime.nodes.phase2 import (
    phase_2_gate,
    phase_2_implement,
    phase_2_plan,
    phase_2_research,
    phase_2_scaffold,
    phase_2_simplify,
)
from half.runtime.nodes.phase3 import (
    phase_3_gate,
    phase_3_integration,
    phase_3_security,
    phase_3_testing,
)
from half.runtime.nodes.phase4 import (
    phase_4_cicd,
    phase_4_gate,
    phase_4_infrastructure,
    phase_4_launch,
)
from half.runtime.nodes.phase5 import (
    phase_5_codify,
    phase_5_gate,
    phase_5_iterate,
    phase_5_observe,
)
from half.runtime.nodes.routing import route_from_finality_gate, route_from_gate

__all__ = [
    "_write_artifact",
    "phase_1_architecture",
    "phase_1_discovery",
    "phase_1_gate",
    "phase_1_specification",
    "phase_2_gate",
    "phase_2_implement",
    "phase_2_plan",
    "phase_2_research",
    "phase_2_scaffold",
    "phase_2_simplify",
    "phase_3_gate",
    "phase_3_integration",
    "phase_3_security",
    "phase_3_testing",
    "phase_4_cicd",
    "phase_4_gate",
    "phase_4_infrastructure",
    "phase_4_launch",
    "phase_5_codify",
    "phase_5_gate",
    "phase_5_iterate",
    "phase_5_observe",
    "route_from_finality_gate",
    "route_from_gate",
]
