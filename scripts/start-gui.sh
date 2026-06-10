#!/usr/bin/env bash
# HALF — Start the Command Center GUI
#
# Usage:
#   ./scripts/start-gui.sh            # Browser mode (default)
#   ./scripts/start-gui.sh --tauri    # Tauri desktop app mode
#
# Browser mode: starts the sidecar HTTP server and opens the HTML frontend.
# Tauri mode: builds and runs the native desktop app.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== HALF Command Center ==="

if [ "${1:-}" = "--tauri" ]; then
    echo "Mode: Tauri Desktop App"
    echo ""
    
    # Check for Rust
    if ! command -v cargo &>/dev/null; then
        echo "ERROR: Rust not found. Install from https://rustup.rs"
        exit 1
    fi
    
    # Check for npm/node
    if ! command -v npm &>/dev/null; then
        echo "WARNING: npm not found. Install Node.js for full Tauri dev experience."
        echo "Falling back to cargo check..."
        cd "$REPO_DIR/src-tauri"
        cargo check
        echo ""
        echo "To run the GUI:"
        echo "  1. Install Node.js: https://nodejs.org"
        echo "  2. cd frontend && npm install"
        echo "  3. npm run tauri dev"
        exit 0
    fi
    
    # Install frontend deps and run
    cd "$REPO_DIR/frontend"
    npm install
    echo ""
    echo "Starting Tauri dev server..."
    npx tauri dev
    
else
    echo "Mode: Browser (HTTP server)"
    echo ""
    echo "Starting sidecar HTTP server on http://127.0.0.1:9722"
    echo "Open dist/index.html in your browser."
    echo ""
    
    cd "$REPO_DIR"
    python3 -m half.half_sidecar serve
fi
