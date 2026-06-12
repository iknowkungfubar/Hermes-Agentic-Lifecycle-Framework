#!/usr/bin/env bash
# Two-pass coverage: main process + subprocesses, then combined
set -euo pipefail
cd "$(dirname "$0")/.."

VENV_PYTHON=".venv/bin/python3"

echo "=== Clean ==="
rm -rf .coverage .coverage.* htmlcov

echo "=== Pass 1: Full suite with pytest-cov ==="
PYTHONPATH=. $VENV_PYTHON -m pytest tests/ -q --tb=no \
  --cov=src/half --cov-config=.coveragerc 2>&1 | grep -E "passed|TOTAL" || true

echo ""
echo "=== Pass 2: Subprocess coverage ==="
PYTHONPATH=. COVERAGE_PROCESS_START=.coveragerc \
  $VENV_PYTHON -m pytest tests/coverage/ tests/tdd/ -q --tb=no -o "addopts=" 2>&1 | grep "passed" || true

echo ""
echo "=== Subprocess coverage files ==="
ls .coverage.* 2>/dev/null | head -5 || echo "(none)"

echo ""
echo "=== Combine ==="
$VENV_PYTHON -m coverage combine 2>&1

echo ""
echo "=== Final Report ==="
$VENV_PYTHON -m coverage report --include="src/half/*" 2>&1 | grep -E "TOTAL|Name"
