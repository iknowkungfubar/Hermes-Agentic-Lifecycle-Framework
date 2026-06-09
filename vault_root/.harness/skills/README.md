# On-Demand Skills Directory

Place complex procedure Markdown scripts here.
They are only injected when called via slash commands from .harness/agents.md.

## Skill List

Add skills as individual .md files with this frontmatter:

```yaml
---
name: skill-name
description: "Brief description"
trigger: "/command-name"
tags: [category]
---
```

## Examples

- `database-migration.md` — Standard DB migration procedure
- `rollback-procedure.md` — Production rollback steps
- `code-review-checklist.md` — Pre-merge review items
