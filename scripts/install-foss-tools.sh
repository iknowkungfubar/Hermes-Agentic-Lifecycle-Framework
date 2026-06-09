#!/usr/bin/env bash
# HALF — FOSS Toolchain Installer
# Installs the CLI-based FOSS tools: garak, bumblebee
# Docker-based tools are managed via docker-compose.foss.yml
#
# Usage: ./scripts/install-foss-tools.sh
set -euo pipefail

echo "=== HALF FOSS Toolchain Installer ==="
echo ""

# ─── NVIDIA garak (LLM Vulnerability Scanner) ─────────────────────────────────
echo "[1/3] NVIDIA garak — LLM vulnerability scanner..."
if command -v garak &>/dev/null; then
    echo "  ✓ garak already installed ($(garak --version 2>/dev/null || echo "unknown version"))"
else
    echo "  Installing garak..."
    pip install garak 2>/dev/null && echo "  ✓ garak installed" || echo "  ⚠ Failed to install garak (try: pip install garak)"
fi

# ─── Perplexity Bumblebee (Supply Chain Scanner) ──────────────────────────────
echo "[2/3] Perplexity Bumblebee — supply chain scanner..."
if command -v bumblebee &>/dev/null; then
    echo "  ✓ bumblebee already installed"
else
    echo "  To install bumblebee (requires Go 1.25+):"
    echo "    go install github.com/perplexityai/bumblebee/cmd/bumblebee@latest"
    echo "  Or download from: https://github.com/perplexityai/bumblebee/releases"
fi

# ─── TruffleHog (Secrets Detection) ───────────────────────────────────────────
echo "[3/3] TruffleHog — secrets scanner..."
if command -v trufflehog &>/dev/null; then
    echo "  ✓ trufflehog already installed"
else
    echo "  Installing trufflehog..."
    pip install trufflehog 2>/dev/null && echo "  ✓ trufflehog installed" || echo "  ⚠ Failed to install trufflehog"
fi

echo ""
echo "=== FOSS Tools Status ==="
echo "  garak:      $(command -v garak &>/dev/null && echo 'installed' || echo 'not installed')"
echo "  bumblebee:  $(command -v bumblebee &>/dev/null && echo 'installed' || echo 'not installed')"
echo "  trufflehog: $(command -v trufflehog &>/dev/null && echo 'installed' || echo 'not installed')"
echo ""
echo "Docker-based tools (start with):"
echo "  docker compose -f docker/docker-compose.foss.yml up -d"
echo "  This deploys: LangWatch, Prometheus, Grafana, PostgreSQL, Redis, Agent Mail"
