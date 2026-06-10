#!/usr/bin/env bash
# HALF — Setup Branch Protection Rules on GitHub
# Enforces the Main-Staging-Feature workflow.
# Usage: ./scripts/setup-branch-protection.sh <org/repo>

set -euo pipefail

REPO="${1:-}"
if [ -z "$REPO" ]; then
    echo "Usage: $0 <org/repo>"
    echo "Example: $0 my-org/my-project"
    exit 1
fi

echo "Setting up branch protection for $REPO"
echo ""

# Protect main branch
echo "--- main branch ---"
gh api "repos/$REPO/branches/main/protection" \
  --method PUT \
  --input - << 'JSON' || echo "  (may already be configured)"
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "type-check", "test", "security"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null
}
JSON

# Protect staging branch
echo "--- staging branch ---"
gh api "repos/$REPO/branches/staging/protection" \
  --method PUT \
  --input - << 'JSON' || echo "  (may already be configured)"
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["lint", "type-check", "test"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON

echo ""
echo "Branch protection configured."
echo "Workflow: feature -> PR -> staging -> verify -> main (via Finality Gate)"
