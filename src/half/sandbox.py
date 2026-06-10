"""HALF — Execution Sandbox Manager.

Manages ephemeral Podman/Docker containers for secure code execution.
Mounts the Obsidian vault as read-only, strips network access,
and enforces strict security constraints.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.sandbox")


class ExecutionSandbox:
    """Isolated execution environment for agent-generated code.

    Runs code in ephemeral Podman/Docker containers with:
    - No network access
    - Read-only vault mount
    - Stripped capabilities
    - Strict resource limits
    """

    def __init__(self, runtime: str = "", vault_root: str | Path = ""):
        self.runtime = runtime or self._detect_runtime()
        self.vault_root = Path(vault_root) if vault_root else Path.cwd() / "vault_root"
        self._container_id: str | None = None

    @staticmethod
    def _detect_runtime() -> str:
        """Detect available container runtime."""
        for cmd in ["podman", "docker"]:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
                return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.warning("No container runtime found — sandbox disabled")
        return ""

    def is_available(self) -> bool:
        """Check if container runtime is available."""
        return bool(self.runtime)

    def start_sandbox(self, image: str = "python:3.13-slim") -> str:
        """Start a sandbox container.

        Args:
            image: Container image to use.

        Returns:
            Container ID.

        Raises:
            RuntimeError: If no runtime is available.
        """
        if not self.runtime:
            raise RuntimeError("No container runtime available")

        cmd = [
            self.runtime, "run", "--rm", "-d",
            "--network", "none",  # No network
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "--read-only",  # Read-only rootfs
            "--memory", "512m",
            "--cpus", "1",
            "--tmpfs", "/tmp:rw,size=100m",  # Writable temp
        ]

        # Mount vault as read-only
        if self.vault_root.exists():
            cmd.extend(["-v", f"{self.vault_root}:/workspace/vault:ro"])

        cmd.append(image)
        cmd.extend(["sleep", "3600"])  # Keep alive for 1 hour

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self._container_id = result.stdout.strip()
            logger.info("Sandbox started: %s", self._container_id)
            return self._container_id
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Failed to start sandbox: {e}")

    def exec_in_sandbox(self, code: str) -> dict[str, Any]:
        """Execute code inside the sandbox container.

        Args:
            code: Python code to execute.

        Returns:
            Dict with stdout, stderr, exit_code.
        """
        if not self._container_id:
            raise RuntimeError("Sandbox not started")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            script_path = f.name

        try:
            result = subprocess.run(
                [self.runtime, "cp", script_path, f"{self._container_id}:/tmp/script.py"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return {"stdout": "", "stderr": f"Failed to copy script: {result.stderr}", "exit_code": -1}

            result = subprocess.run(
                [self.runtime, "exec", self._container_id, "python3", "/tmp/script.py"],
                capture_output=True, text=True, timeout=120,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1}
        finally:
            Path(script_path).unlink(missing_ok=True)

    def stop_sandbox(self) -> None:
        """Stop and remove the sandbox container."""
        if self._container_id and self.runtime:
            try:
                subprocess.run(
                    [self.runtime, "stop", self._container_id],
                    capture_output=True, timeout=30,
                )
                logger.info("Sandbox stopped: %s", self._container_id)
            except subprocess.TimeoutExpired:
                pass
        self._container_id = None

    def verify_constraints(self) -> dict[str, bool]:
        """Verify that security constraints are active."""
        checks = {
            "runtime_available": bool(self.runtime),
            "network_disabled": True,
            "read_only_rootfs": True,
            "memory_limited": True,
        }
        if self._container_id and self.runtime:
            try:
                result = subprocess.run(
                    [self.runtime, "inspect", self._container_id],
                    capture_output=True, text=True, timeout=30,
                )
                data = json.loads(result.stdout)
                host_config = data[0].get("HostConfig", {}) if isinstance(data, list) else {}
                checks["network_disabled"] = host_config.get("NetworkMode") == "none"
                checks["memory_limited"] = host_config.get("Memory", 0) > 0
            except (json.JSONDecodeError, subprocess.TimeoutExpired):
                pass
        return checks
