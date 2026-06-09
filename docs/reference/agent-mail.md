# Agent Mail

**Agent Mail** provides decentralized task coordination by granting agents
memorable email identities, searchable message histories, and voluntary
file reservation leases to avoid stepping on each other.

## Architecture

- Backed by **SQLite** with WAL mode for concurrent access
- **Git** audit trail — every action creates a commit
- Exposed as an **MCP server** for tool integration

## Agent Identities

Agents are addressed as `name@half.local`. Registration creates a
persistent identity with role metadata:

- `coder-1@half.local` — Implementation agent
- `reviewer-1@half.local` — Code review agent
- `security-1@half.local` — Security auditor

## Message Types

| Type | Description |
|------|-------------|
| `direct` | One-to-one message |
| `broadcast` | All agents |
| `request_contact` | Handshake |
| `task_assignment` | Assign a task |
| `file_reservation` | Reserve a file |
| `file_release` | Release a reservation |
| `crp` | Consultation Request Pack |
| `ack` | Acknowledgment |

## File Leases

Agents acquire leases on files they intend to modify, preventing
conflicting changes. Leases expire after 2 hours by default.

## Running

```bash
# Start the MCP server
python -m src.agent_mail.server

# Or via Docker
docker compose -f docker/docker-compose.foss.yml up agent-mail -d
```
