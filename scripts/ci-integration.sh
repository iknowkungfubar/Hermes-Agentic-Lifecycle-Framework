#!/usr/bin/env bash
# HALF — CI Integration Test Runner
# Starts all required infrastructure, runs integration tests, cleans up.
# Usage: bash scripts/ci-integration.sh

set -euo pipefail

HALF_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HALF_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${YELLOW}→${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     HALF CI Integration Test Runner      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Start HTTP Sidecar ───────────────────────────────────────────────────
info "Starting HTTP sidecar on :9721..."
pkill -f "half.http_sidecar" 2>/dev/null || true
sleep 1
PYTHONPATH=. .venv/bin/python -m half.http_sidecar &
SIDECAR_PID=$!
sleep 2

if curl -sf http://127.0.0.1:9721/api/status > /dev/null 2>&1; then
  pass "HTTP sidecar running (PID $SIDECAR_PID)"
else
  fail "HTTP sidecar failed to start"
  exit 1
fi

# ─── Create Test Audio File ───────────────────────────────────────────────
info "Creating test audio file..."
HALF_TEST_AUDIO=$(mktemp /tmp/half-test-audio-XXXXXX.wav)
python3 -c "
import struct, wave
with wave.open('$HALF_TEST_AUDIO', 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(struct.pack('<' + 'h' * 16000, *[0]*16000))
" 2>/dev/null && pass "Test audio file created" || info "Could not create audio file"
export HALF_TEST_AUDIO

# ─── Create Test Git Repo ────────────────────────────────────────────────
info "Creating test git repo..."
HALF_TEST_REPO=$(mktemp -d /tmp/half-test-repo-XXXXXX)
cd "$HALF_TEST_REPO"
git init -q
git config user.email "ci@half.local"
git config user.name "CI Runner"
echo "# Test Repo" > README.md
mkdir -p src tests .harness
echo "print('hello')" > src/main.py
echo "def test(): pass" > tests/test_example.py
echo "# Rules" > .harness/agents.md
git add -A && git commit -q -m "init"
cd "$HALF_DIR"
export HALF_TEST_REPO
pass "Test git repo at $HALF_TEST_REPO"

# ─── Create No-Slop Test Files ────────────────────────────────────────────
HALF_TEST_NOSLOP=$(mktemp -d /tmp/half-test-noslop-XXXXXX)
mkdir -p "$HALF_TEST_NOSLOP"/{src/a,src/b,src/a/sub}
echo "import os" > "$HALF_TEST_NOSLOP/src/a/x.py"
echo "def foo(): return 42" > "$HALF_TEST_NOSLOP/src/b/y.py"
echo "class Helper: pass" > "$HALF_TEST_NOSLOP/src/a/sub/z.py"
export HALF_TEST_NOSLOP
pass "No-slop test files created"

# ─── Create PSM Test Skills ──────────────────────────────────────────────
HALF_TEST_PSM=$(mktemp -d /tmp/half-test-psm-XXXXXX)
mkdir -p "$HALF_TEST_PSM"
cat > "$HALF_TEST_PSM/test-skill.yaml" << EOF
name: test-skill
version: "1.0"
description: "A test skill for CI"
author: "CI Runner"
EOF
export HALF_TEST_PSM
pass "PSM test skills created"

# ─── Run Tests ────────────────────────────────────────────────────────────
echo ""
info "Running integration tests..."
echo ""

PYTHONPATH=. .venv/bin/pytest tests/integration/ -v --tb=short \
  -o "markers=integration: Integration tests requiring infrastructure" \
  2>&1 | tee /tmp/half-integration-results.txt

INTEGRATION_EXIT_CODE=${PIPESTATUS[0]}

# ─── Run Full Suite with Coverage ─────────────────────────────────────────
echo ""
info "Running full test suite with coverage..."
echo ""

PYTHONPATH=. .venv/bin/pytest tests/ -q --tb=no \
  --cov=src/half --cov-report=term-missing \
  -o "markers=integration" 2>&1 | tee /tmp/half-coverage-results.txt

# ─── Cleanup ──────────────────────────────────────────────────────────────
info "Cleaning up..."
kill $SIDECAR_PID 2>/dev/null || true
rm -f "$HALF_TEST_AUDIO" 2>/dev/null || true
rm -rf "$HALF_TEST_REPO" 2>/dev/null || true
rm -rf "$HALF_TEST_NOSLOP" 2>/dev/null || true
rm -rf "$HALF_TEST_PSM" 2>/dev/null || true
pass "Cleanup done"

echo ""
if grep -q "TOTAL" /tmp/half-coverage-results.txt; then
  grep "TOTAL" /tmp/half-coverage-results.txt
fi

# Check integration test results
if grep -q "failed" /tmp/half-integration-results.txt 2>/dev/null; then
  FAILED=$(grep "failed" /tmp/half-integration-results.txt | grep -oP '\d+(?= failed)' || echo "0")
else
  FAILED=0
fi

if [ "$FAILED" -gt 0 ]; then
  echo ""
  fail "$FAILED integration test(s) failed"
  exit 1
else
  pass "All integration tests passed"
fi
