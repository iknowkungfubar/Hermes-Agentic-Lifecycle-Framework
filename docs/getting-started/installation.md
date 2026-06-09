# Installation

## Prerequisites

- **Python 3.13+** — Required runtime
- **Git** — For version control
- **uv** (recommended) or pip — Package manager
- **Rust** (optional) — For building the Tauri Command Center GUI
- **Docker** (optional) — For running the FOSS observability stack

## Install from Source

```bash
# Clone the repository
git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git
cd Hermes-Agentic-Lifecycle-Framework

# Install uv (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv sync --group dev

# Verify installation
half version
```

## Install via pip (when published)

```bash
pip install hermes-half
```

## Verify

Run the test suite to verify everything is working:

```bash
make test
```

You should see output like:
```
======================== 62 passed in 0.68s =========================
```

## Optional Dependencies

### Tauri Command Center GUI

```bash
# Requires Rust
cargo install tauri-cli
cd src-tauri
cargo build --release
```

### Whisper.cpp (Voice STT)

```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make
# Download model
./models/download-ggml-model.sh large-v3-q5_0
```

### Piper (Voice TTS)

```bash
# Download from https://github.com/rhasspy/piper/releases
# Or use package manager
pip install piper-tts
```

### FOSS Observability Stack

```bash
docker compose -f docker/docker-compose.foss.yml up -d
```

This starts: LangWatch, Laminar, Prometheus, Grafana, PostgreSQL, Redis, Agent Mail, Focalboard
