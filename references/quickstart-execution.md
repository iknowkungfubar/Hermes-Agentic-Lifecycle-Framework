# HALF Quick-Start Execution Guide

## One-Command Launch

When the user says any of these triggers, load the `half` skill and begin:

| Trigger | Mode |
|---------|------|
| "Build [concept]" | full |
| "Run HALF on [idea]" | full |
| "Prototype [feature]" | prototype |
| "Audit this repo" | audit |
| "Fix this bug" | patch |

## Execution Sequence

```bash
## Step 1: Create workspace
mkdir -p .hale/artifacts/phase-{1,2,3,4,5}
mkdir -p .hale/logs
mkdir -p .hale/gates

## Step 2: Load HALF
skill_view(name="half")
# Follow Phase 1→2→3→4→5 sequence defined in SKILL.md

## Step 3: After each phase, run the gate
echo "=== PHASE N GATE CHECK ==="
# Run checks from phase gate YAML
# Log result to .hale/gates/phase-N.json
```

## Per-Phase Time Estimates

| Phase | Time (new project) | Time (existing repo) |
|-------|-------------------|---------------------|
| Discovery & Strategy | 30-60 min | 15-30 min |
| Development & Coding | 2-8 hours (per subsystem) | 30min-2h per feature |
| Quality Assurance | 1-3 hours | 30min-1h |
| Polish & Deployment | 30min-2 hours | 15-30 min |
| Iteration | Ongoing | 15min per cycle |

## Phase Product Checklist (Gate Summary)

### Phase 1 Gate (before coding begins)
```
□ REQUIREMENTS.md — covers all capabilities, users, constraints
□ SPECIFICATION.md — FRs, NFRs, API contracts, data model
□ TASKS.md — dependency graph, acceptance criteria per task
□ ARCHITECTURE.md — components, data flow, ADRs
□ Human has reviewed and approved → PROCEED
```

### Phase 2 Gate (before QA begins)
```
□ All tasks implemented per dependency graph
□ Tests pass (pytest — 0 failures)
□ Lint passes (ruff — 0 errors)
□ Type check passes (mypy strict — 0 errors)
□ Coverage ≥ 80%
□ No circular imports
→ PROCEED TO QA
```

### Phase 3 Gate (before deployment begins)
```
□ Coverage ≥ 80% line, ≥ 70% branch
□ All FRs have tests
□ No CRITICAL security findings
□ Integration tests pass
□ Contract tests match spec
□ Human has reviewed test + security report → PROCEED
```

### Phase 4 Gate (before release)
```
□ All CI checks pass
□ Docker build succeeds (image < 500MB)
□ Health endpoint returns 200
□ Smoke tests pass
□ Rollback plan exists
□ Monitoring configured
□ Human has reviewed launch readiness → PROCEED
```

### Phase 5 Gate (ongoing)
```
□ Monitoring loops active
□ Issue triage documented
□ No critical issues older than 7 days
□ Codification Imperative active
```

## Common Failure Modes & Resolutions

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Tests fail on CI but pass locally | Different env | Pin exact versions, use Docker for CI |
| Coverage below threshold | Tests only cover happy paths | Run HALF-Testing to auto-generate gap tests |
| Security scan finds CRITICAL | Hardcoded secret/unvalidated input | Run Fix-As-You-Go immediately |
| Docker build too large | No multi-stage build | Add .dockerignore, use distroless base |
| Integration tests fail | API contract mismatch | Run contract test suite, fix response schemas |
| Pipeline stuck at human checkpoint | Missing context or unclear question | Generate specific question with decision options |
