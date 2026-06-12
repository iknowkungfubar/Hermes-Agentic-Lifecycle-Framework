# HALF — Production Docker Image
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python package
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/

RUN pip install --no-cache-dir -e .

# Expose API ports
EXPOSE 9721 9722 31337

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9721/api/health', timeout=5)" || exit 1

# Default: run the HTTP sidecar
CMD ["python3", "-m", "half.http_sidecar"]
