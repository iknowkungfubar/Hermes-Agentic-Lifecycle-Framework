# Quick Start

Get HALF running in under 5 minutes.

## 1. Install

```bash
# From PyPI (no repo needed)
pip install hermes-half

# Or from source
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework
pip install -e .
```

## 2. Verify

```bash
half version
# → HALF v1.0.1

half status
# → {"status": "ok", "project": "default", ...}
```

## 3. Start the API Server

In a separate terminal:

```bash
cd ~/Hermes-Agentic-Lifecycle-Framework
python -m half.http_sidecar
```

## 4. Open the GUI

```bash
cd ~/Hermes-Agentic-Lifecycle-Framework
./src-tauri/target/release/half-command-center
```

The Command Center shows:
- **Left pane**: Pipeline phase progress + error budget
- **Center pane**: PDA chat — type commands like `status`, `help`, `run phase 2`
- **Right pane**: Finality Gate + stalled node monitor

## 5. Chat with the Commander Agent

Type these commands in the PDA chat:

| Command | What it does |
|---------|-------------|
| `help` | Show available commands |
| `status` | Show pipeline state |
| `run phase 2` | Execute development phase |
| `gate check phase 1` | Run gate checks |
| `generate mrp` | Create Merge-Readiness Pack |
| `deploy` | Deployment sign-off instructions |

## 6. Run Tests

```bash
# Full test suite
pytest tests/ -q

# With coverage
pytest tests/ -q --cov=src/half --cov-report=term-missing

# Integration tests (requires sidecar running)
pytest tests/integration/ -q
```

## 7. Start Full Environment (with services)

```bash
# Option A: Setup script (recommended)
bash scripts/setup.sh

# Option B: Manual
python -m half.http_sidecar &                          # REST API
podman-compose -f docker/docker-compose.foss.yml up -d  # Prometheus, Grafana
```

### Available Endpoints

Once the sidecar is running:

```bash
curl http://127.0.0.1:9721/api/health         # → {"status": "ok", "version": "1.0.1"}
curl http://127.0.0.1:9721/api/status         # → Pipeline state
curl http://127.0.0.1:9721/api/vram           # → GPU VRAM usage
curl http://127.0.0.1:9721/api/stalled        # → Stalled agent nodes
curl -X POST http://127.0.0.1:9721/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"status"}'                   # → Chat with PDA
```

## Next Steps

- [Installation Guide](installation.md) — Full setup with native engines
- [First Project](first-project.md) — Walk through the 5-phase pipeline
- [User Guide](../guide/overview.md) — Architecture and concepts
- [CLI Reference](../reference/cli.md) — All CLI commands
