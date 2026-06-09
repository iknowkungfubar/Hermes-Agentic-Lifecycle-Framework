"""
HALF-Infrastructure Agent (Phase 4A)

Generates Docker, Kubernetes, and serverless deployment configurations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class InfrastructureAgent:
    """Phase 4A: IaC generation for Docker, Kubernetes, and serverless."""

    def __init__(self, project_name: str = "app"):
        self.project_name = project_name

    DOCKERFILE_CONTENT = """\
# Multi-stage build for {project_name}
FROM python:3.13-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev

FROM python:3.13-slim AS production

WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY src/ src/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

CMD [".venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    DOCKER_COMPOSE_CONTENT = """\
version: "3.8"

services:
  app:
    build:
      context: .
      target: production
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app
      - REDIS_URL=redis://cache:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: "512M"

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  cache:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
"""

    def generate_dockerfile(self, target_dir: Path) -> str:
        """Generate a multi-stage Dockerfile."""
        content = self.DOCKERFILE_CONTENT.format(project_name=self.project_name)
        filepath = target_dir / "Dockerfile"
        filepath.write_text(content)
        return str(filepath)

    def generate_docker_compose(self, target_dir: Path) -> str:
        """Generate a docker-compose.yml with health checks."""
        content = self.DOCKER_COMPOSE_CONTENT
        filepath = target_dir / "docker-compose.yml"
        filepath.write_text(content)
        return str(filepath)

    def generate_dotenv_example(self, target_dir: Path) -> str:
        """Generate .env.example with all required variables."""
        content = f"""\
# {self.project_name} — Environment Configuration
# Copy this to .env and fill in values.

# Application
SECRET_KEY=change-me-to-a-random-secret
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/app
REDIS_URL=redis://localhost:6379/0

# External Services
# SENTRY_DSN=
# OTEL_EXPORTER_OTLP_ENDPOINT=
"""
        filepath = target_dir / ".env.example"
        filepath.write_text(content)
        return str(filepath)

    def generate_kubernetes_manifests(self, target_dir: Path) -> dict[str, str]:
        """Generate Kubernetes deployment manifests."""
        created: dict[str, str] = {}

        deployment = f"""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.project_name}
  labels:
    app: {self.project_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {self.project_name}
  template:
    metadata:
      labels:
        app: {self.project_name}
    spec:
      containers:
      - name: {self.project_name}
        image: {self.project_name}:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {self.project_name}
spec:
  selector:
    app: {self.project_name}
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
"""

        k8s_dir = target_dir / "kubernetes"
        k8s_dir.mkdir(parents=True, exist_ok=True)

        filepath = k8s_dir / "deployment.yaml"
        filepath.write_text(deployment)
        created[str(filepath)] = deployment

        return created
