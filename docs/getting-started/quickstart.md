# Quick Start

Get from zero to running HALF in under 5 minutes.

## 1. Install

```bash
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework
pip install uv
uv sync --group dev
make test  # Verify everything works
```

## 2. Bootstrap a Project

```bash
./scripts/genesis.sh --project my-api --mode full
cd my-api
```

This creates:
- `.hale/` — HALF workspace with artifacts, gates, logs, checkpoints
- `.goal/config.yaml` — Goal CLI configuration
- `.harness/agents.md` — MentorScript (agent context)
- `.hale/loopscript.yaml` — DAG execution plan
- `.hale/finality-gate.json` — Finality Gate (locked)
- `AGENTS.md` — Project context for AI agents

## 3. Run the HALF Pipeline

In your Hermes Agent session:

```bash
skill_view(name="half")
```

Then execute the 5-phase sequence:

| Phase | Command | Duration | Gate |
|-------|---------|----------|------|
| Phase 1 | `skill_view(name="half")` → Phase 1 | ~45 min | G1 (completeness) |
| Phase 2 | Auto-dispatch via dependency graph | ~4 hours | G2 (tests pass) |
| Phase 3 | Parallel red-teaming | ~2 hours | G3 (no CRITICAL) |
| Phase 4 | IaC + CI/CD generation | ~1 hour | G4 (health check) |
| Phase 5 | Monitoring loops | Ongoing | G5 (active) |

## 4. Monitor Progress

```bash
half status              # Pipeline status
half gate-check phase-1  # Run Phase 1 gate checks
```

## 5. Deploy

When Phase 4 completes, the Finality Gate unlocks:

```bash
half generate-mrp  # Generate Merge-Readiness Pack
```

Review the MRP, then sign off via the Tauri GUI or:

```bash
# Via the Command Center Finality Gate panel
```

## What's Next?

- [Your First Project](first-project.md) — Detailed walkthrough
- [User Guide](../guide/overview.md) — Complete framework documentation
- [CLI Reference](../reference/cli.md) — All CLI commands
