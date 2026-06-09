# Getting Started: Your First HALF Project

This guide walks through building a "Task Management API" using HALF.

## Step 1: Bootstrap

```bash
half init --project task-api --mode full
cd task-api
```

Check what was created:

```bash
ls -la .hale/
```

## Step 2: Discovery & Strategy (Phase 1)

Load the HALF framework in your Hermes Agent session:

```bash
skill_view(name="half")
```

Follow Phase 1A-1C to produce:

```bash
ls .hale/artifacts/phase-1/
# 01-REQUIREMENTS.md  02-SPECIFICATION.md  03-TASKS.md
# 04-ARCHITECTURE.md  05-ADRs.md
```

Run the gate check:

```bash
half gate-check phase-1
```

## Step 3: Development (Phase 2)

With the spec approved, Phase 2 runs the Tri-Phasic Loop:

1. **Research** — Agent analyzes the codebase (read-only)
2. **Plan** — Agent writes `.spec.md` (design-only)
3. **Implement** — Agent writes code + tests (write-restricted)
4. **Simplify** — Code-Simplifier refactoring pass

```bash
half run-phase phase-2
half gate-check phase-2
```

## Step 4: Quality Assurance (Phase 3)

```bash
half run-phase phase-3
half gate-check phase-3
```

## Step 5: Deploy (Phase 4)

```bash
half run-phase phase-4
half gate-check phase-4
half generate-mrp
```

## Step 6: Iterate (Phase 5)

```bash
half run-phase phase-5
half gate-check phase-5
```
