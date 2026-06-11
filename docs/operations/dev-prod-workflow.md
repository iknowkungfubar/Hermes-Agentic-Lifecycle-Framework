# HALF — Dev/Production Workflow Guide

## Two-Repo Strategy

```
Public Dev Repo (origin)          Private Production Repo (production)
┌────────────────────────┐        ┌──────────────────────────────┐
│ iknowkungfubar/        │        │ your-org/hermes-half-prod    │
│ Hermes-Agentic-        │  ──►   │ (private GitHub)             │
│ Lifecycle-Framework    │ merge  │                              │
│                        │        │ Contains:                    │
│ Public: MIT license    │        │ - All dev code               │
│ All features           │        │ - Private configs/secrets    │
│ Open to contributions  │        │ - Production credentials     │
│                        │        │ - Internal tooling           │
│ Purpose: Staging/OSS   │        │ - Deploy-specific configs    │
└────────────────────────┘        └──────────────────────────────┘
         ▲                                    │
         │ git push origin master              │ git pull production master
         │                                    ▼
   GitHub (public)                    Private GitHub (paid/org)
```

## Setup Instructions

### Step 1: Create the Private Repo on GitHub

```bash
# Using gh CLI (requires authentication)
gh repo create hermes-half-prod --private --description "HALF Production Version"

# Or manually at https://github.com/new
# - Repository name: hermes-half-prod
# - Visibility: Private
# - Do NOT initialize with README/.gitignore (we'll push existing)
```

### Step 2: Add the Private Repo as a Remote

```bash
# From your local repo
cd Hermes-Agentic-Lifecycle-Framework

# Add production remote
git remote add production https://github.com/your-org/hermes-half-prod.git

# Verify
git remote -v
# origin       https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git (fetch)
# origin       https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git (push)
# production   https://github.com/your-org/hermes-half-prod.git (fetch)
# production   https://github.com/your-org/hermes-half-prod.git (push)
```

### Step 3: Create the Production Branch

```bash
# Create a production branch from current master
git checkout -b production

# Push to private repo
git push production production

# Set upstream
git branch --set-upstream-to=production/production

# Switch back to dev
git checkout master
```

### Step 4: Configure Git for Multiple Remotes

Add this to `.git/config` or run:

```bash
# Pull dev changes into production
git config remote.production.fetch "+refs/heads/*:refs/remotes/production/*"

# Default push to production (safety: only push production branch)
git config remote.production.push refs/heads/production:refs/heads/production
```

### Step 5: Production-Only Files (never pushed to public)

Create a `.gitignore` override for the production branch:

```bash
# Files that exist ONLY in production (not in dev)
cat >> .git/info/exclude << 'EOF'
# Production-only overrides
.env
*.pem
production-config.yaml
deploy-keys/
secrets/
EOF
```

Or better: add production-specific files to a `production/` directory that's in `.gitignore` on the dev branch but tracked on production:

```bash
mkdir -p production/secrets
echo "secrets/" >> .gitignore
# On production branch, remove from gitignore:
# git checkout production
# # Edit .gitignore to remove secrets/ line
# git add production/
# git commit -m "chore: add production configuration"
```

## Daily Workflow

### Push changes from dev to production:

```bash
# On dev branch — work normally
git checkout master
# ... make changes, commit ...
git push origin master  # Push to public dev

# When ready to release to production:
git checkout production
git merge master
git push production production
git checkout master
```

### Pull production-only changes back to dev (rare):

```bash
git checkout production
# Make production-specific changes
git commit -am "chore: update production config"
git push production production

# If dev needs something from production:
git checkout master
git cherry-pick <commit-hash>
```

### Production-specific branches:

```bash
# For hotfixes that bypass dev staging
git checkout production
git checkout -b hotfix/critical-fix
# ... fix ...
git commit -am "fix: critical production issue"
git checkout production
git merge hotfix/critical-fix
git push production production
```

## Security Considerations

1. **Never push `.env` or secrets** to the public repo
2. Use `.env.example` for documentation (already done)
3. Production credentials go in the private repo only
4. The `production/` directory is tracked only on production branch
5. Consider GitHub Actions secrets for CI/CD tokens

## Automation

For automated sync from dev to production, add a GitHub Action to the
production repo:

```yaml
# .github/workflows/sync-from-dev.yml (in production repo)
name: Sync from Dev
on:
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: iknowkungfubar/Hermes-Agentic-Lifecycle-Framework
          ref: master
      - run: |
          git remote add production https://${{ secrets.PAT }}@github.com/your-org/hermes-half-prod.git
          git push production master:production
```

## Quick Reference

```bash
# Dev workflow
git checkout master
git add -A && git commit -m "feat: ..."
git push origin master

# Release to production
git checkout production
git merge master
# Resolve any conflicts
git push production production
git checkout master

# Production hotfix
git checkout production
# fix...
git commit -am "fix: ..."
git push production production
```
