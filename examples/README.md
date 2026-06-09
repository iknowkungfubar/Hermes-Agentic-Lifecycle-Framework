# HALF Example: API Service Walkthrough
# This directory contains example outputs from running HALF on a hypothetical
# "Task Management API" project. Use these as reference when running your own projects.

## Example Output Structure

```
examples/api-service/phase-1/
├── 01-REQUIREMENTS.md     # Requirements document
├── 02-SPECIFICATION.md    # Technical specification
├── 03-TASKS.md            # Task decomposition
├── 04-ARCHITECTURE.md     # Ideal State Architecture
└── 05-ADRs.md             # Architecture Decision Records
```

## Quick Reference

When running HALF on your own project:
1. Create workspace: `mkdir -p .hale/workspace/<project>`
2. Load the framework: `skill_view(name="half")`
3. Run Phase 1: `./scripts/run-phase.sh phase-1 <project>`
4. Run gate check: `./scripts/gate-check.sh phase-1`
5. Proceed through phases 2-5

## Example Project: Task Management API

This example demonstrates a RESTful task management API with:
- User authentication (JWT)
- CRUD operations for tasks
- PostgreSQL persistence
- Redis caching
- Docker deployment
