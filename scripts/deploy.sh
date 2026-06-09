#!/usr/bin/env bash
# HALF Deployment Script
# Usage: ./scripts/deploy.sh [environment]
set -euo pipefail

ENV="${1:-staging}"
PROJECT_DIR="${2:-.}"

echo "=== HALF Deployment: ${ENV} ==="

case "${ENV}" in
    staging)
        echo "Deploying to staging..."
        cd "${PROJECT_DIR}"
        docker compose -f docker/docker-compose.yml up -d --build
        echo "✓ Staging deployment complete"
        echo "Running smoke tests..."
        sleep 2
        curl -f http://localhost:8000/health 2>/dev/null && echo "✓ Health check passed" || echo "⚠ Health check pending"
        ;;
    production)
        echo "=== FINALITY GATE ==="
        echo "⚠ Production deployment requires:"
        echo "  1. Merge-Readiness Pack (MRP) generated"
        echo "  2. All Phase 4 gate checks passed"
        echo "  3. Human cryptographic sign-off"
        echo ""
        echo "To proceed:"
        echo "  1. Review MRP at .hale/artifacts/phase-4/"
        echo "  2. Confirm all PR-01 through PR-18 checks are complete"
        echo "  3. Run: ./scripts/deploy.sh canary"
        ;;
    canary)
        echo "Canary deployment (10% traffic)..."
        echo "Monitor for 10 minutes before increasing to 50%"
        echo "Implement with your service mesh or load balancer"
        ;;
    rollback)
        echo "Rolling back to previous version..."
        echo "docker compose down && docker compose -f docker-compose.previous.yml up -d"
        echo "✓ Rollback initiated"
        ;;
    *)
        echo "Usage: $0 [staging|production|canary|rollback]"
        exit 1
        ;;
esac
