#!/usr/bin/env bash
# HALF Gate Check Runner
# Usage: ./scripts/gate-check.sh <phase> [project-dir]
set -euo pipefail

PHASE="${1:-}"
PROJECT_DIR="${2:-.}"
HALF_DIR="${PROJECT_DIR}/.hale"

if [ -z "${PHASE}" ]; then
    echo "Usage: $0 <phase> [project-dir]"
    echo "  Phases: phase-1, phase-2, phase-3, phase-4, phase-5"
    exit 1
fi

echo "=== HALF Gate Check: ${PHASE} ==="

case "${PHASE}" in
    phase-1)
        FAIL=0
        for f in 01-REQUIREMENTS.md 02-SPECIFICATION.md 03-TASKS.md 04-ARCHITECTURE.md 05-ADRs.md; do
            if [ -f "${HALF_DIR}/artifacts/phase-1/${f}" ]; then
                echo "  ✓ ${f} found"
            else
                echo "  ✗ ${f} MISSING"
                FAIL=1
            fi
        done
        if [ "${FAIL}" -eq 0 ]; then
            echo "GATE: PHASE 1 PASSED"
        else
            echo "GATE: PHASE 1 FAILED — missing artifacts"
        fi
        exit ${FAIL}
        ;;
    phase-2)
        echo "GATE: PHASE 2"
        echo "  Check: tests pass?      pytest"
        echo "  Check: lint errors?      ruff check"
        echo "  Check: type errors?      mypy"
        echo "  Check: coverage ≥80%?    pytest --cov"
        echo ""
        echo "Run manually:"
        echo "  pytest --cov=src/ --cov-fail-under=80 && ruff check src/ && mypy src/"
        ;;
    phase-3)
        echo "GATE: PHASE 3"
        for f in test-quality-report.md security-scan.md red-team-report.md integration-test-report.md; do
            if [ -f "${HALF_DIR}/artifacts/phase-3/${f}" ]; then
                echo "  ✓ ${f} found"
            else
                echo "  - ${f} not required (may be generated)"
            fi
        done
        ;;
    phase-4)
        echo "GATE: PHASE 4"
        for f in rollback-plan.md production-readiness.md; do
            if [ -f "${HALF_DIR}/artifacts/phase-4/${f}" ]; then
                echo "  ✓ ${f} found"
            else
                echo "  - ${f} not required"
            fi
        done
        ;;
    phase-5)
        echo "GATE: PHASE 5 (monitoring)"
        echo "  Verify monitoring loops are active"
        echo "  Verify Codification Imperative is active"
        ;;
    *)
        echo "Unknown phase: ${PHASE}"
        exit 1
        ;;
esac

echo "Gate check logged to ${HALF_DIR}/gates/${PHASE}.log"
mkdir -p "${HALF_DIR}/gates"
date > "${HALF_DIR}/gates/${PHASE}.log"
