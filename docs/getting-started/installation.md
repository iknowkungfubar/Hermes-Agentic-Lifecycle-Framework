# Installation

## Prerequisites

- **Python 3.13+** — Required runtime
- **Git** — For version control
- **uv** (recommended) or pip — Package manager
- **Rust** (optional) — For building the Tauri Command Center GUI
- **Podman or Docker** (optional) — For running the FOSS observability stack

## Quick Install (pip)

```bash
pip install hermes-half
half version
# → HALF v1.0.1
```

## Install from Source

```bash
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework

# Install with uv (recommended)
pip install uv
uv sync --group dev
pip install -e .

# Or with pip
pip install -e ".[dev]"

# Verify
half version
```

## Full Setup (with all services)

```bash
# Run the setup script to install native engines and start services
bash scripts/setup.sh

# Or step by step:
# 1. Install Python package (above)
# 2. Start the HTTP API sidecar
python -m half.http_sidecar &

# 3. Start observability stack (requires Podman/Docker)
podman-compose -f docker/docker-compose.foss.yml up -d

# 4. Build the Tauri GUI (requires Rust)
cd src-tauri && cargo build --release
```

## Docker Image

```bash
# Build
podman build -t hermes-half:latest -f docker/Dockerfile .

# Run
podman run -p 9721:9721 hermes-half:latest
```

## What Gets Installed

| Component | Location | Purpose |
|-----------|----------|---------|
| CLI (`half`) | `~/.local/bin/half` | Pipeline orchestration commands |
| Python package | `hermes-half` on PyPI | Core framework library |
| HTTP sidecar | `python -m half.http_sidecar` | REST API for GUI and integrations |
| Tauri GUI | `src-tauri/target/release/half-command-center` | Desktop Command Center |
| Agent Mail DB | `.hale/agent-mail/mail.db` | Inter-agent message store |
| Native Whisper | `.whisper/build/bin/whisper-cli` | Speech-to-text engine |
| Native Piper | `.piper/build/piper/piper` | Text-to-speech engine |

## Verification

```bash
half version                # → HALF v1.0.1
half status                 # → JSON pipeline state
curl http://127.0.0.1:9721/api/health  # → {"status": "ok", "version": "1.0.1"}
pytest tests/ -q            # → 875+ passed
```
