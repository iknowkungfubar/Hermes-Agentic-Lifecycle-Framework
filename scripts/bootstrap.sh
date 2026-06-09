#!/usr/bin/env bash
# HALF Bootstrap Script
# Initializes the Hermes Agentic Lifecycle Framework environment
set -euo pipefail

HALF_DIR="${HALF_DIR:-$(pwd)/.hale}"

echo "=== HALF Bootstrap ==="
echo "Target: ${HALF_DIR}"
echo ""

# Create directory structure
mkdir -p "${HALF_DIR}"/{artifacts/{phase-1,phase-2,phase-3,phase-4,phase-5},gates,logs,metrics,state/checkpoints}

echo "✓ Directory structure created"

# Copy default templates if they don't exist
TEMPLATES_DIR="$(dirname "$0")/../templates"
if [ -d "${TEMPLATES_DIR}" ]; then
    for tmpl in fail-safes.yaml gap-report.md; do
        if [ ! -f "${HALF_DIR}/${tmpl}" ] && [ -f "${TEMPLATES_DIR}/${tmpl}" ]; then
            cp "${TEMPLATES_DIR}/${tmpl}" "${HALF_DIR}/${tmpl}"
            echo "✓ Copied template: ${tmpl}"
        fi
    done
fi

echo ""
echo "=== HALF Bootstrap Complete ==="
echo ""
echo "To start a new project:"
echo "  export PROJECT_NAME=\"my-project\""
echo "  mkdir -p .hale/workspace/\${PROJECT_NAME}"
echo "  skill_view(name=\"half\")"
echo ""
echo "Status: ${HALF_DIR}"
ls -la "${HALF_DIR}"
