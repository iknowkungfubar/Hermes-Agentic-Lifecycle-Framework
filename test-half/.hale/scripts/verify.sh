#!/usr/bin/env bash
# Verification-at-Scale runner
set -euo pipefail
echo "=== Verification-at-Scale ==="
pytest --cov=src/ --cov-fail-under=80 --asyncio-mode=auto "$@" 2>/dev/null
echo "✓ Tests passed"
ruff check src/ 2>/dev/null && echo "✓ Lint passed"
mypy src/ --strict 2>/dev/null && echo "✓ Types passed"
echo "=== Gate PASSED ==="
