#!/usr/bin/env bash
# Run a specific HALF phase
# Usage: ./scripts/run-phase.sh <phase> <project-name>
set -euo pipefail

PHASE="${1:-}"
PROJECT="${2:-demo}"
HALF_DIR=".hale"

if [ -z "${PHASE}" ]; then
    echo "Usage: $0 <phase> [project-name]"
    echo "  Phases: phase-1, phase-2, phase-3, phase-4, phase-5"
    exit 1
fi

PHASE_DIR="${HALF_DIR}/artifacts/${PHASE}"
mkdir -p "${PHASE_DIR}"

echo "=== HALF Phase Runner ==="
echo "Phase:    ${PHASE}"
echo "Project:  ${PROJECT}"
echo "Output:   ${PHASE_DIR}"
echo ""

case "${PHASE}" in
    phase-1)
        echo "PHASE 1: Discovery & Strategy"
        echo "Steps:"
        echo "  1A: HALF-Discovery — Requirements discovery"
        echo "  1B: HALF-Specification — Technical specification"
        echo "  1C: HALF-Architect — Ideal State Architecture"
        echo ""
        echo "Artifacts to produce:"
        echo "  ${PHASE_DIR}/01-REQUIREMENTS.md"
        echo "  ${PHASE_DIR}/02-SPECIFICATION.md"
        echo "  ${PHASE_DIR}/03-TASKS.md"
        echo "  ${PHASE_DIR}/04-ARCHITECTURE.md"
        echo "  ${PHASE_DIR}/05-ADRs.md"
        ;;
    phase-2)
        echo "PHASE 2: Development & Coding"
        echo "Steps:"
        echo "  2A: HALF-Scaffold — Repository scaffolding"
        echo "  2B: HALF-Implement — Harness-first TDD"
        echo ""
        echo "Use delegate_task for parallel dependency-graph dispatch"
        ;;
    phase-3)
        echo "PHASE 3: Quality Assurance"
        echo "Steps:"
        echo "  3A: HALF-Testing — Test suite completeness"
        echo "  3B: HALF-Security — SAST + red-teaming"
        echo "  3C: HALF-Integration — Integration + contract tests"
        ;;
    phase-4)
        echo "PHASE 4: Polish & Deployment"
        echo "Steps:"
        echo "  4A: HALF-Infrastructure — IaC generation"
        echo "  4B: HALF-CICD — CI/CD pipeline"
        echo "  4C: HALF-Launch — Production readiness"
        ;;
    phase-5)
        echo "PHASE 5: Iteration"
        echo "Steps:"
        echo "  5A: HALF-Observe — Monitoring loops"
        echo "  5B: HALF-Iterate — Issue triage"
        echo "  5C: HALF-Codify — Codification Imperative"
        ;;
    *)
        echo "Unknown phase: ${PHASE}"
        echo "Valid phases: phase-1, phase-2, phase-3, phase-4, phase-5"
        exit 1
        ;;
esac

echo ""
echo "Phase directory ready: ${PHASE_DIR}"
echo "Run 'skill_view(name=\"half\")' for full execution instructions"
