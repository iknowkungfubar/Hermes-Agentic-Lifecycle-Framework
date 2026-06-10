#!/usr/bin/env bash
# HALF — Branch Management: Main-Staging-Feature workflow
# Enforces the branching strategy from the blueprint.
#
# Usage:
#   ./scripts/branch.sh start feature/my-feature
#   ./scripts/branch.sh submit feature/my-feature
#   ./scripts/branch.sh merge-to-staging feature/my-feature
#   ./scripts/branch.sh release

set -euo pipefail

BRANCH="${2:-}"
COMMAND="${1:-help}"

case "$COMMAND" in
    start)
        if [ -z "$BRANCH" ]; then
            echo "Usage: $0 start <branch-name>"
            exit 1
        fi
        git checkout -b "$BRANCH" staging
        echo "Created branch '$BRANCH' from staging"
        ;;
    
    submit)
        if [ -z "$BRANCH" ]; then
            echo "Usage: $0 submit <branch-name>"
            exit 1
        fi
        # Create PR against staging
        gh pr create \
            --base staging \
            --head "$BRANCH" \
            --title "feat: $(echo "$BRANCH" | sed 's|feature/||;s|fix/||;s|refactor/||')" \
            --body "Automated PR from branch '$BRANCH'"
        echo "PR created for '$BRANCH' -> staging"
        ;;
    
    merge-to-staging)
        if [ -z "$BRANCH" ]; then
            echo "Usage: $0 merge-to-staging <branch-name>"
            exit 1
        fi
        echo "=== Verification-at-Scale ==="
        echo "Running tests..."
        pytest tests/ -q --tb=short || { echo "Tests failed — block merge"; exit 1; }
        echo "Running lint..."
        ruff check src/ || { echo "Lint failed — block merge"; exit 1; }
        echo "Running type check..."
        mypy src/ || { echo "Type check failed — block merge"; exit 1; }
        echo ""
        echo "All checks passed. Merging '$BRANCH' -> staging..."
        git checkout staging
        git merge "$BRANCH" --no-ff -m "merge: $BRANCH -> staging"
        echo "Merged '$BRANCH' into staging"
        ;;
    
    release)
        echo "=== Finality Gate ==="
        echo "Running full verification..."
        pytest tests/ -q --tb=short || { echo "Tests failed"; exit 1; }
        ruff check src/ || { echo "Lint failed"; exit 1; }
        mypy src/ || { echo "Type check failed"; exit 1; }
        
        echo ""
        echo "All checks passed."
        echo "To release staging -> main:"
        echo "  1. Generate MRP: half generate-mrp"
        echo "  2. Review MRP at .hale/artifacts/phase-4/mrp.json"
        echo "  3. Approve in Command Center Finality Gate"
        echo "  4. Then run: git checkout main && git merge staging --no-ff"
        ;;
    
    *)
        echo "HALF Branch Manager"
        echo ""
        echo "Commands:"
        echo "  start <name>         Create feature branch from staging"
        echo "  submit <name>        Create PR for branch -> staging"
        echo "  merge-to-staging <n> Test + merge branch into staging"
        echo "  release              Verify and prepare for main merge"
        ;;
esac
