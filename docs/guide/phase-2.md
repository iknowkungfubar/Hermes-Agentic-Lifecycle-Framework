# Phase 2: Development & Coding

**Objective:** Implement the codebase with mandatory TDD using the Tri-Phasic Execution Loop.

## Tri-Phasic Execution Loop

1. **Research (Read-Only)** — Agent analyzes codebase with grep/cat/AST parsers. No file modifications.
2. **Plan (Design-Only)** — Agent outputs `.spec.md`. Must pass Critic review.
3. **Implement (Write-Restricted)** — Code written in ephemeral sandbox. Harness-first TDD.
4. **Simplify** — Code-Simplifier refactoring pass (reduce nesting, extract methods).

## Steps

- **2A: Repository Scaffolding** — Project structure, tooling config, CI setup
- **2B: Tri-Phasic Implementation** — Research → Plan → Implement → Simplify

## Gate Check (G2)

- G2.1: All FR-IDs have corresponding implementation
- G2.2: All tasks have passing tests
- G2.3: Lint passes (0 errors)
- G2.4: Type check passes (strict mode)
- G2.5: Coverage ≥80%
- G2.6: No circular imports
