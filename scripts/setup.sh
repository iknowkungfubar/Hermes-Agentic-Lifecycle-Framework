#!/usr/bin/env bash
# HALF — Complete Setup Script
# Installs everything needed to run the full HALF 1.5 stack:
#   Python package, native engines, Docker stack, eBPF
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework/master/scripts/setup.sh | bash
#   # Or locally:
#   bash scripts/setup.sh
#
# Supports: --no-docker, --no-voice, --no-ebpf, --no-pglite flags

set -euo pipefail

HALF_DIR="${HALF_DIR:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
cd "$HALF_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
info() { echo -e "  ${YELLOW}→${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     HALF 1.5 — Setup                     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Parse flags
SKIP_DOCKER=false; SKIP_VOICE=false; SKIP_EBPF=false; SKIP_PGLITE=false
for arg in "$@"; do
  case "$arg" in --no-docker) SKIP_DOCKER=true;; --no-voice) SKIP_VOICE=true;; --no-ebpf) SKIP_EBPF=true;; --no-pglite) SKIP_PGLITE=true;; esac
done

# ─── Phase 1: Python Package ─────────────────────────────────────────────
info "Installing Python package..."
if uv pip install -e . 2>/dev/null; then
  pass "hermes-half installed via uv"
elif pip install -e . 2>/dev/null; then
  pass "hermes-half installed via pip"
else
  fail "Could not install Python package — try: pip install hermes-half"
fi

# ─── Phase 2: Whisper.cpp (STT) ─────────────────────────────────────────
if [ "$SKIP_VOICE" = false ]; then
  info "Building Whisper.cpp..."
  if [ -d .whisper ]; then
    pass "Whisper.cpp already cloned"
  else
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git .whisper 2>/dev/null
    cd .whisper && make -j4 2>/dev/null && cd ..
    pass "Whisper.cpp built"
  fi
  if [ ! -f .whisper/models/ggml-tiny.en.bin ]; then
    info "Downloading Whisper model (75MB)..."
    cd .whisper && bash models/download-ggml-model.sh tiny.en 2>/dev/null && cd ..
    pass "Whisper model downloaded"
  fi
fi

# ─── Phase 3: Piper (TTS) ───────────────────────────────────────────────
if [ "$SKIP_VOICE" = false ]; then
  info "Installing Piper TTS..."
  if [ -f .piper/build/piper/piper ]; then
    pass "Piper already installed"
  else
    mkdir -p .piper/build
    wget -q https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz -O .piper/piper.tar.gz
    tar xzf .piper/piper.tar.gz -C .piper/build/
    rm .piper/piper.tar.gz
    pass "Piper binary installed"
  fi
  if [ ! -f .piper/voices/en_US-lessac-medium.onnx ]; then
    info "Downloading Piper voice model (61MB)..."
    mkdir -p .piper/voices
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -O .piper/voices/en_US-lessac-medium.onnx
    pass "Piper voice model downloaded"
  fi
fi

# ─── Phase 4: PGlite WASM ───────────────────────────────────────────────
if [ "$SKIP_PGLITE" = false ]; then
  info "Installing PGlite WASM..."
  if [ -d node_modules/@electric-sql/pglite ]; then
    pass "PGlite already installed"
  else
    npm install @electric-sql/pglite 2>/dev/null
    pass "PGlite installed"
  fi
fi

# ─── Phase 5: Docker Stack (Prometheus + Grafana) ───────────────────────
if [ "$SKIP_DOCKER" = false ]; then
  info "Deploying observability stack..."
  if command -v podman &>/dev/null; then
    cp docker/prometheus.yml /tmp/prometheus.yml && chmod 644 /tmp/prometheus.yml
    podman rm -f half-prometheus half-grafana 2>/dev/null || true
    podman run -d --name half-prometheus --network host --security-opt label=disable \
      -v /tmp/prometheus.yml:/etc/prometheus/prometheus.yml:ro,Z \
      docker.io/prom/prometheus:latest 2>/dev/null && pass "Prometheus started" || fail "Prometheus failed"
    podman run -d --name half-grafana --network host \
      -e GF_SECURITY_ADMIN_PASSWORD=change-me \
      docker.io/grafana/grafana:latest 2>/dev/null && pass "Grafana started" || fail "Grafana failed"
  elif command -v docker &>/dev/null; then
    docker compose -f docker/docker-compose.foss.yml up -d 2>/dev/null && pass "Docker stack started" || fail "Docker stack failed"
  else
    info "No container runtime found — skip with --no-docker"
  fi
fi

# ─── Phase 6: eBPF Grimlock ──────────────────────────────────────────────
if [ "$SKIP_EBPF" = false ]; then
  info "Compiling eBPF Grimlock..."
  if command -v clang &>/dev/null; then
    clang -O2 -target bpf -c config/grimlock.c -o config/grimlock.o 2>/dev/null && pass "eBPF compiled" || info "eBPF compilation skipped (no BPF headers)"
  else
    info "clang not found — skip with --no-ebpf"
  fi
fi

# ─── Phase 7: Verify ─────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Verification                          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

half version 2>/dev/null && pass "CLI: half version" || fail "CLI not in PATH"
uv pip install hermes-half 2>/dev/null && pass "PyPI: hermes-half" || info "Not published to PyPI"
[ -f .whisper/build/bin/whisper-cli ] && pass "Whisper: $(.whisper/build/bin/whisper-cli --version 2>&1 | head -1)" || true
[ -f .piper/build/piper/piper ] && pass "Piper: $({ .piper/build/piper/piper --help 2>&1 | head -1 || true; })" || true
[ -d node_modules/@electric-sql/pglite ] && pass "PGlite: installed" || true
pgrep half-prometheus &>/dev/null && pass "Prometheus: running on :9090" || true
pgrep half-grafana &>/dev/null && pass "Grafana: running on :3000" || true
[ -f config/grimlock.o ] && pass "eBPF: grimlock.o ($(wc -c < config/grimlock.o)B)" || true

echo ""
echo "  HALF 1.5 setup complete."
echo "  Run 'half version' to verify the CLI."
echo ""
