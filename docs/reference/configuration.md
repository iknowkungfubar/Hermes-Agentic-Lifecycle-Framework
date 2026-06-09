# Configuration Reference

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HALF_DB_PASSWORD` | `half_secret` | PostgreSQL password for observability stack |
| `HALF_GRAFANA_PASSWORD` | `change-me` | Grafana admin password |
| `HALF_LANGWATCH_SECRET` | `change-me-in-production` | LangWatch NextAuth secret |
| `HALF_AGENT_MAIL_DB` | `.hale/agent-mail/mail.db` | Agent Mail database path |

## .goal/config.yaml

```yaml
default_provider: lmstudio
budgets:
  per_goal_usd: 5.0
  per_ticket_usd: 0.5
  hard_stop: true
roles:
  planner: { model: opencode/gpt-5.1-codex }
  coder: { model: qwen2.5-coder:7b }
  reviewer: { model: deepseek/deepseek-v4-pro }
```

## .hale/config.yaml

```yaml
version: "1.0"
project: my-app
mode: full
fail_safe:
  enabled: true
  max_retries: 3
error_budget:
  window_days: 30
  total_points: 100
```
