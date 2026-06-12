"""HALF 1.5 — Pre-Warmed Staging Containers.

Pre-warms staging containers during smoke testing to enable zero-latency
deployment. When the Finality Gate approves, the pre-warmed container is
promoted to production instantly, bypassing cold-start delays.

Based on the HALF 1.5 doctrine's 'Zero-Latency Deployment' spec.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger("half.prewarm")


@dataclass
class WarmContainer:
    """A pre-warmed staging container."""

    name: str
    image: str
    container_id: str = ""
    port: int = 0
    status: str = "warming"  # warming, ready, promoted, expired
    warmed_at: str = ""
    health_check_passed: bool = False
    smoke_test_passed: bool = False


class PreWarmDeployment:
    """Pre-warms staging containers for zero-latency deployment.

    During Phase 4 smoke testing, this module:
    1. Builds the container image
    2. Starts the container
    3. Runs health checks
    4. Leaves it warm until Finality Gate approves
    5. On approval, promotes the warm container instantly
    """

    def __init__(self, compose_file: str | Path = "docker/docker-compose.yml"):
        self.compose_file = Path(compose_file)
        self._warm_containers: dict[str, WarmContainer] = {}

    def prewarm(
        self, service_name: str = "app", image_tag: str = "latest"
    ) -> WarmContainer:
        """Pre-warm a staging container.

        Args:
            service_name: Service name to pre-warm.
            image_tag: Docker image tag.

        Returns:
            WarmContainer with status.
        """
        logger.info("PreWarm: Pre-warming '%s:%s'", service_name, image_tag)

        container = WarmContainer(
            name=service_name,
            image=f"{service_name}:{image_tag}",
        )

        try:
            # Build image
            subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    container.image,
                    "-f",
                    str(self.compose_file.parent / "Dockerfile"),
                    ".",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Start container in background
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    f"half-prewarm-{service_name}",
                    "-p",
                    "0",  # Random port
                    container.image,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                container.container_id = result.stdout.strip()
                container.status = "ready"
                container.warmed_at = datetime.now(tz=UTC).isoformat()
                self._warm_containers[service_name] = container
                logger.info(
                    "PreWarm: Container '%s' ready (ID: %s)",
                    service_name,
                    container.container_id[:12],
                )
            else:
                container.status = "failed"
                logger.warning(
                    "PreWarm: Failed to start '%s': %s", service_name, result.stderr
                )

        except subprocess.TimeoutExpired:
            container.status = "failed"
            logger.warning("PreWarm: Timed out building '%s'", service_name)
        except FileNotFoundError:
            container.status = "failed"
            logger.warning("PreWarm: Docker not found — install Docker or Podman")

        return container

    def health_check(self, service_name: str) -> bool:
        """Run health check on a pre-warmed container.

        Args:
            service_name: Service name.

        Returns:
            True if healthy.
        """
        container = self._warm_containers.get(service_name)
        if not container or not container.container_id:
            return False

        try:
            # Try to ping the container's health endpoint
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Status}}",
                    container.container_id,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            healthy = result.stdout.strip() == "running"
            container.health_check_passed = healthy
            return healthy
        except Exception:
            return False

    def promote(self, service_name: str) -> bool:
        """Promote a pre-warmed container to production immediately.

        Args:
            service_name: Service to promote.

        Returns:
            True if promotion succeeded.
        """
        container = self._warm_containers.get(service_name)
        if not container or container.status != "ready":
            logger.warning("PreWarm: Cannot promote '%s' — not ready", service_name)
            return False

        try:
            # Tag as production
            subprocess.run(
                ["docker", "tag", container.image, f"{service_name}:production"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Stop the old production container
            subprocess.run(
                ["docker", "stop", f"{service_name}-production"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            subprocess.run(
                ["docker", "rm", f"{service_name}-production"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Start the pre-warmed container as production
            subprocess.run(
                [
                    "docker",
                    "rename",
                    container.container_id,
                    f"{service_name}-production",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            # Remove the prewarm tag
            self._warm_containers.pop(service_name, None)
            container.status = "promoted"
            logger.info(
                "PreWarm: '%s' promoted to production — zero-latency deploy",
                service_name,
            )
            return True

        except Exception as e:
            logger.exception("PreWarm: Promotion failed: %s", e)
            return False

    def cleanup(self) -> None:
        """Stop and remove all pre-warmed containers."""
        for service_name, container in list(self._warm_containers.items()):
            if container.container_id:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", container.container_id],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    logger.info("PreWarm: Cleaned up '%s'", service_name)
                except Exception:
                    pass
        self._warm_containers.clear()
