# Changelog

All notable changes to the Hermes Agentic Lifecycle Framework (HALF) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-09

### Added
- Complete 5-phase SDLC framework: Discovery & Strategy, Development & Coding,
  Quality Assurance, Polish & Deployment, Iteration
- 16 agent skill modules covering all phases (HALF-Discovery through HALF-Codify)
- LangGraph state machine runtime with WAL checkpointer and human-interrupt gates
- Git-backed Agent Mail with decentralized coordination and file reservation leases
- Voice engine (Whisper.cpp STT + Piper TTS) for air-gapped voice commands
- Focalboard Kanban integration for ticket/phase tracking
- Tauri 2.0 desktop Command Center GUI with 3-pane layout
- Finality Gate with cryptographic sign-off for production deployment
- FOSS observability stack: LangWatch, Laminar, Prometheus, Grafana
- CI/CD pipeline templates with per-stage quality gates
- Error budget tracking with automatic pipeline health monitoring
- Fail-safe protocol with 3-level escalation (step → phase → human)
- Tri-phasic execution loop: Research (read-only) → Plan (design-only) → Implement (write-restricted)
- Code-Simplifier refactoring pass with AST-based static analysis
- MentorScript and LoopScript DAG for declarative agent SOPs
- Obsidian vault structure for dual-layer context engine
- Genesis bootstrap script for zero-config project initialization
- 62 automated tests across all modules
- Makefile with install, lint, typecheck, test, and ship targets
- Pre-commit hooks for code quality automation
- Full MkDocs-compatible documentation site

### Security
- CVE-2025-67644 mitigation: metadata allowlist validation for LangGraph SQLite
- CVE-2026-28277 mitigation: JSON-safe serialization instead of msgpack
- Execution sandbox constraints with read-only vault mounts
- Dangerous command denylist and path traversal protection
