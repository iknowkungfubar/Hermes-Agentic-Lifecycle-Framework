# HALF — Hermes Agentic Lifecycle Framework
# https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework

.PHONY: all install test lint typecheck format clean distclean ci ready ship

# ─── Default ──────────────────────────────────────────────────────────────────

all: install lint typecheck test

# ─── Installation ─────────────────────────────────────────────────────────────

install:
	uv sync --group dev

install-foss:
	./scripts/install-foss-tools.sh

genesis:
	./scripts/genesis.sh

# ─── Quality ──────────────────────────────────────────────────────────────────

lint:
	uv run ruff check src/ tests/

lint-fix:
	uv run ruff check --fix --unsafe-fixes src/ tests/

typecheck:
	uv run mypy src/

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

# ─── Testing ──────────────────────────────────────────────────────────────────

test:
	PYTHONPATH=. uv run pytest tests/ -v --tb=short

test-quick:
	PYTHONPATH=. uv run pytest tests/ -q --tb=no

test-cov:
	PYTHONPATH=. uv run pytest tests/ --cov=src/ --cov-report=term-missing --cov-report=html

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

distclean: clean
	rm -rf .venv
	rm -rf src-tauri/target

# ─── CI / Ready Check ─────────────────────────────────────────────────────────

ci: install lint typecheck test

ready: ci
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════╗"
	@echo "║  HALF — All checks passed. Ready for launch.            ║"
	@echo "╚═══════════════════════════════════════════════════════════╝"

# ─── Ship (full release build) ────────────────────────────────────────────────

ship: ready
	@echo "Building Tauri Command Center..."
	cd src-tauri && cargo build --release
	@echo "HALF build complete: src-tauri/target/release/half-command-center"
