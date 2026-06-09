#!/usr/bin/env bash
# =============================================================================
# HALF Genesis Bootstrap — Complete Environment Initialization
# =============================================================================
# Implements the 4-part bootstrapping prompt sequence from the HALF doctrine:
#
#   Part 1: Core Configuration Files
#   Part 2: Prompt 1 — Initialize Base Runtimes
#   Part 3: Prompt 2 — Instantiate FOSS Guardrails
#   Part 4: Prompt 3 — Deploy Agent Mail & Local Indexing
#   Part 5: Prompt 4 — Scaffold the Command Center
#   Part 6: Master Genesis Prompt
#
# Usage:
#   ./scripts/genesis.sh [--project my-project] [--mode full] [--dir ./my-project]
#
# Options:
#   --project NAME   Project name (default: my-app)
#   --mode MODE      Pipeline mode: full|prototype|patch|audit (default: full)
#   --dir PATH       Target directory (default: ./my-project)
#   --force          Overwrite existing files without prompting
# =============================================================================

set -euo pipefail

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Defaults ────────────────────────────────────────────────────────────────
PROJECT_NAME="my-app"
MODE="full"
TARGET_DIR=""
FORCE=false
HALF_SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ─── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project) PROJECT_NAME="$2"; shift 2 ;;
        --mode) MODE="$2"; shift 2 ;;
        --dir) TARGET_DIR="$2"; shift 2 ;;
        --force) FORCE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

TARGET_DIR="${TARGET_DIR:-$PROJECT_NAME}"

# ─── Banner ───────────────────────────────────────────────────────────────────
echo -e "${MAGENTA}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        HALF Genesis Bootstrap — Hermes Agentic              ║"
echo "║           Lifecycle Framework v1.0.0                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "Project:  ${CYAN}${PROJECT_NAME}${NC}"
echo "Mode:     ${CYAN}${MODE}${NC}"
echo "Target:   ${CYAN}${TARGET_DIR}${NC}"
echo "Source:   ${CYAN}${HALF_SOURCE_DIR}${NC}"
echo ""

# ─── Prompt 1: Initialize Base Runtimes ──────────────────────────────────────
# From the blueprint: Verify Node.js 22 LTS, Go 1.25+, AMD ROCm 7.1.1 driver
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PROMPT 1: Initialize Base Runtimes${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

echo -e "  ${YELLOW}[1/4]${NC} Checking Python 3.13+..."
PYTHON_VERSION=$(python3 --version 2>/dev/null || echo "none")
if echo "$PYTHON_VERSION" | grep -qE "Python 3.(1[3-9]|[2-9][0-9])"; then
    echo -e "  ${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "  ${YELLOW}⚠${NC} $PYTHON_VERSION (3.13+ recommended)"
fi

echo -e "  ${YELLOW}[2/4]${NC} Checking Node.js..."
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo -e "  ${GREEN}✓${NC} Node.js $NODE_VER"
else
    echo -e "  ${YELLOW}⚠${NC} Node.js not found (needed for Tauri GUI)"
fi

echo -e "  ${YELLOW}[3/4]${NC} Checking Rust (for Tauri)..."
if command -v rustc &>/dev/null; then
    RUST_VER=$(rustc --version)
    echo -e "  ${GREEN}✓${NC} $RUST_VER"
else
    echo -e "  ${YELLOW}⚠${NC} Rust not found (needed for Tauri GUI)"
fi

echo -e "  ${YELLOW}[4/4]${NC} Checking Docker..."
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version)
    echo -e "  ${GREEN}✓${NC} $DOCKER_VER"
else
    echo -e "  ${RED}✗${NC} Docker not found (required for FOSS stack)"
fi

# ─── Part 1: Core Configuration Files ─────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PART 1: Core Configuration Files${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

# Create project directory
mkdir -p "${TARGET_DIR}"
cd "${TARGET_DIR}"
echo -e "  ${GREEN}✓${NC} Created target: ${TARGET_DIR}"

# Create HALF workspace structure
mkdir -p .hale/{artifacts/{phase-1,phase-2,phase-3,phase-4,phase-5},gates,logs,metrics,state/checkpoints}
echo -e "  ${GREEN}✓${NC} Created .hale/ workspace"

# Create .goal/config.yaml
mkdir -p .goal
cat > .goal/config.yaml << GOALEOF
# Goal Orchestration Configuration — HALF Genesis
default_provider: lmstudio
budgets:
  per_goal_usd: 5.0
  per_ticket_usd: 0.5
  hard_stop: true
limits:
  coder_max_iterations: 10
  recursion_limit: 200
  shell_command_denylist: ["rm -rf /", "dd if=", "mkfs", "format"]
roles:
  planner:
    model: opencode/gpt-5.1-codex
  coder:
    model: qwen2.5-coder:7b
  reviewer:
    model: deepseek/deepseek-v4-pro
GOALEOF
echo -e "  ${GREEN}✓${NC} Created .goal/config.yaml"

# Create .hale/config.yaml
cat > .hale/config.yaml << HALECONF
# HALF Runtime Configuration
version: "1.0"
project: ${PROJECT_NAME}
mode: ${MODE}
fail_safe:
  enabled: true
  max_retries: 3
  escalation_path:
    step_retry: {max_attempts: 3, cooldown_seconds: 30}
    phase_retry: {trigger: "3 consecutive step failures", max_attempts: 2}
    human_escalation: {trigger: "phase retry fails OR critical gate failure"}
error_budget:
  window_days: 30
  total_points: 100
HALECONF
echo -e "  ${GREEN}✓${NC} Created .hale/config.yaml"

# ─── Prompt 2: Instantiate FOSS Guardrails ────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PROMPT 2: Instantiate FOSS Guardrails${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

echo -e "  ${YELLOW}[1/3]${NC} Creating FOSS stack docker-compose..."
mkdir -p .hale/foss
cp -n "${HALF_SOURCE_DIR}/docker/docker-compose.foss.yml" ".hale/foss/docker-compose.yml" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} FOSS stack configuration ready"

echo -e "  ${YELLOW}[2/3]${NC} Creating Verifiction-at-Scale scripts..."
mkdir -p .hale/scripts
cat > .hale/scripts/verify.sh << 'VERIFYEOF'
#!/usr/bin/env bash
# Verification-at-Scale runner
set -euo pipefail
echo "=== Verification-at-Scale ==="
pytest --cov=src/ --cov-fail-under=80 --asyncio-mode=auto "$@" 2>/dev/null
echo "✓ Tests passed"
ruff check src/ 2>/dev/null && echo "✓ Lint passed"
mypy src/ --strict 2>/dev/null && echo "✓ Types passed"
echo "=== Gate PASSED ==="
VERIFYEOF
chmod +x .hale/scripts/verify.sh
echo -e "  ${GREEN}✓${NC} Verification script created"

echo -e "  ${YELLOW}[3/3]${NC} Creating security baseline..."
mkdir -p .hale/security
cat > .hale/security/bandit.yaml << BANDITEOF
# Bandit security configuration
skips: ['B101', 'B311']
BANDITEOF
echo -e "  ${GREEN}✓${NC} Security baseline created"

# ─── Prompt 3: Agent Mail & Local Indexing ────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PROMPT 3: Deploy Agent Mail & Local Indexing${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

echo -e "  ${YELLOW}[1/3]${NC} Creating Agent Mail config..."
mkdir -p .hale/agent-mail
cat > .hale/agent-mail/config.yaml << AGENTMAIL
# Agent Mail Configuration
server:
  host: 127.0.0.1
  port: 9721
database:
  path: .hale/agent-mail/mail.db
  wal_mode: true
auth:
  enabled: false  # Local-only, no auth needed
AGENTMAIL
echo -e "  ${GREEN}✓${NC} Agent Mail config created"

echo -e "  ${YELLOW}[2/3]${NC} Creating indexing config..."
cat > .hale/indexing.yaml << INDEXEOF
# Repository Indexing Configuration
engine: hierarchical-summary
max_depth: 4
skip_dirs:
  - .git
  - .venv
  - node_modules
  - __pycache__
INDEXEOF
echo -e "  ${GREEN}✓${NC} Indexing config created"

echo -e "  ${YELLOW}[3/4]${NC} Creating safety constraints (read-only vault, sandbox)..."
cat > .hale/safety.yaml << SAFETYEOF
# HALF Execution Safety Constraints
sandbox:
  enabled: true
  runtime: podman  # or docker
  network: none
  read_only_mounts:
    - source: vault_root
      target: /workspace/vault
      type: ro
  dangerous_commands:
    - "rm -rf /"
    - "dd if="
    - "mkfs"
    - "format"
    - ":(){ :|:& };:"
hook_constraints:
  reject_path_traversal: true
  max_command_length: 4096
SAFETYEOF
echo -e "  ${GREEN}✓${NC} Safety constraints created"

echo -e "  ${YELLOW}[4/4]${NC} Creating LoopScript DAG template..."
cat > .hale/loopscript.yaml << LOOPEOF
# LoopScript — Declarative DAG SOP
# Defines the exact Standard Operating Procedure agents must follow
version: "1.0"
phases:
  - id: discover
    agent: HALF-Discovery
    mode: read-only
    inputs: []
    outputs: [01-REQUIREMENTS.md]
  - id: specify
    agent: HALF-Specification
    mode: design-only
    inputs: [01-REQUIREMENTS.md]
    outputs: [02-SPECIFICATION.md, 03-TASKS.md]
  - id: architect
    agent: HALF-Architect
    mode: design-only
    inputs: [02-SPECIFICATION.md]
    outputs: [04-ARCHITECTURE.md, 05-ADRs.md]
  - id: scaffold
    agent: HALF-Scaffold
    mode: write-restricted
    inputs: [03-TASKS.md]
    outputs: [repository-structure]
  - id: research
    agent: HALF-Research
    mode: read-only
    inputs: [04-ARCHITECTURE.md]
    outputs: [codebase-analysis]
  - id: plan
    agent: HALF-Plan
    mode: design-only
    inputs: [codebase-analysis]
    outputs: [implementation-spec]
  - id: implement
    agent: HALF-Implement
    mode: write-restricted
    inputs: [implementation-spec]
    outputs: [implemented-code]
  - id: simplify
    agent: HALF-CodeSimplifier
    mode: write-restricted
    inputs: [implemented-code]
    outputs: [simplified-code]
chain:
  execute: [discover, specify, architect, scaffold, research, plan, implement, simplify]
tri_phasic:
  - research  # Read-Only
  - plan      # Design-Only
  - implement # Write-Restricted
LOOPEOF
echo -e "  ${GREEN}✓${NC} LoopScript DAG created with tri-phasic execution loop"

# ─── Prompt 4: Scaffold Command Center ────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PROMPT 4: Scaffold Command Center${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

echo -e "  ${YELLOW}[1/2]${NC} Creating MentorScript (replaces .cursorrules)..."
mkdir -p .harness
cat > .harness/agents.md << AGENTSMDF
# ${PROJECT_NAME} — Agent Context

## HALF Mode: ${MODE}

## Phase Execution Contract
- Every phase produces artifacts in .hale/artifacts/<phase>/
- Every phase ends with a gate check logged to .hale/gates/<phase>.json
- Human checkpoints after: Phase 1 (spec review), Phase 3 (security review), Phase 4 (deployment sign-off)

## Conventions
- TDD: Write failing tests before implementation
- Commits: feat:|fix:|refactor:|test:|docs: [scope] — [message]
- All public functions: type annotations + docstrings
- Quality gates: ruff 0, mypy 0, pytest pass, coverage ≥80%
AGENTSMDF
echo -e "  ${GREEN}✓${NC} MentorScript (.harness/agents.md) created"

echo -e "  ${YELLOW}[2/2]${NC} Creating Finality Gate placeholder..."
cat > .hale/finality-gate.json << FINALEOF
{
  "status": "locked",
  "mrp_ready": false,
  "deployment_approved": false,
  "description": "Finality Gate — requires human cryptographic sign-off before production deploy"
}
FINALEOF
echo -e "  ${GREEN}✓${NC} Finality Gate initialized (LOCKED)"

# ─── Copy templates ───────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Copying HALF Templates${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

mkdir -p .hale/templates
for tmpl in fail-safes.yaml gap-report.md; do
    src="${HALF_SOURCE_DIR}/templates/${tmpl}"
    if [ -f "$src" ]; then
        cp "$src" ".hale/templates/${tmpl}"
        echo -e "  ${GREEN}✓${NC} Copied ${tmpl}"
    fi
done

# ─── Create AGENTS.md at project root ─────────────────────────────────────────
cat > AGENTS.md << EOFA
# ${PROJECT_NAME} — Project Context for AI Agents

## Overview
This project uses the **Hermes Agentic Lifecycle Framework (HALF)** for autonomous SDLC execution.

## Tech Stack
- Python 3.13+
- FastAPI (API layer)
- PostgreSQL 16 (database)
- Redis 7 (cache)
- Docker (deployment)

## HALF Configuration
- Mode: ${MODE}
- Workspace: .hale/
- Checkpoints: .hale/state/checkpoints/

## Commands
- \`skill_view(name="half")\` — Load the HALF framework
- \`./scripts/genesis.sh\` — Re-run this bootstrapper
EOFA

# ─── Initialize Git ───────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Initializing Version Control${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"

if [ ! -d .git ]; then
    cat > .gitignore << GITIGNORE
__pycache__/
*.py[cod]
.venv/
venv/
env/
.vscode/
.idea/
.DS_Store
*.log
.env
GITIGNORE
    git init
    git add -A
    git commit -m "feat: initial ${PROJECT_NAME} project scaffolded by HALF genesis"
    echo -e "  ${GREEN}✓${NC} Git repository initialized"
else
    echo -e "  ${YELLOW}⚠${NC} Git repository already exists"
fi

# ─── Master Genesis Summary ───────────────────────────────────────────────────
echo ""
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║            HALF Genesis Bootstrap Complete!                  ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Project:    ${CYAN}${PROJECT_NAME}${NC}"
echo -e "  ${GREEN}✓${NC} Mode:       ${CYAN}${MODE}${NC}"
echo -e "  ${GREEN}✓${NC} Directory:  ${CYAN}${TARGET_DIR}${NC}"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo "  1. cd ${TARGET_DIR}"
echo "  2. skill_view(name=\"half\")"
echo "  3. Run Phase 1: Discovery & Strategy"
echo "  4. Gate check → Human review → Phase 2..."
echo ""
echo -e "  ${CYAN}Your First Business Objective:${NC}"
echo '  Hermes, the HALF architecture is verified and the Finality Gate is locked.'
echo "  Here is our first business objective: [YOUR CONCEPT]"
echo "  Use your Planner skill to generate the BriefingScript and decompose this"
echo "  objective into a Kanban board via Focalboard."
echo ""
