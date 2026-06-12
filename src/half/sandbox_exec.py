"""HALF 1.5 — Sandboxed Test Execution.

Runs pytest, mypy, and ruff check inside a headless, network-isolated
Podman or Docker container. Captures stderr and pipes it back for
forced patching via the Self-Correction Loop.

Based on the HALF 1.5 doctrine's 'Sandboxed Test Execution' spec.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("half.sandbox")


@dataclass
class SandboxResult:
    """Result of sandboxed test execution."""

    passed: bool = False
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    container_id: str = ""
    duration_seconds: float = 0.0
    commands_run: list[str] = field(default_factory=list)


class SandboxExecutor:
    """Executes tests inside an isolated container.

    Uses Podman (preferred) or Docker fallback. Container is:
    - Network-isolated (no internet access)
    - Ephemeral (removed after execution)
    - Volume-mounted to the project directory (read-only for source)

    Usage:
        sandbox = SandboxExecutor()
        result = sandbox.run_tests("pytest tests/ -q")
        if not result.passed:
            print(result.stderr)  # Pipe this into self-correct loop
    """

    def __init__(self, runtime: str = "", image: str = "python:3.13-slim"):
        self.runtime = runtime or self._detect_runtime()
        self.image = image
        self._container_id = ""

    def _detect_runtime(self) -> str:
        """Detect available container runtime."""
        for cmd in ["podman", "docker"]:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
                return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.warning("Sandbox: No container runtime found — running tests on host")
        return ""

    def run_tests(
        self,
        command: str = "python3 -m pytest tests/ -q --tb=short",
        workdir: str | Path = ".",
    ) -> SandboxResult:
        """Run a test command inside a sandboxed container.

        Args:
            command: Shell command to execute inside the container.
            workdir: Host directory to mount into the container.

        Returns:
            SandboxResult with stdout, stderr, and pass/fail.
        """
        import time

        start = time.time()
        result = SandboxResult(commands_run=[command])

        if not self.runtime:
            # No container runtime — run directly
            return self._run_direct(command, workdir)

        try:
            # Create ephemeral container
            create_cmd = [
                self.runtime,
                "run",
                "--rm",
                "--network",
                "none",  # Network-isolated
                "--read-only",  # Read-only rootfs
                "-v",
                f"{Path(workdir).resolve()}:/workspace:ro",  # Source read-only
                "-v",
                f"{Path(workdir).resolve()}/.hale:/workspace/.hale:rw",  # Logs writable
                "--security-opt",
                "no-new-privileges",
                "--cap-drop",
                "ALL",
                self.image,
                "sh",
                "-c",
                f"cd /workspace && {command}",
            ]

            proc = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            result.stdout = proc.stdout
            result.stderr = proc.stderr
            result.exit_code = proc.returncode
            result.passed = proc.returncode == 0

        except subprocess.TimeoutExpired:
            result.stderr = "Sandbox execution timed out (300s)"
        except FileNotFoundError:
            logger.warning(
                "Sandbox: %s not found — falling back to direct execution", self.runtime
            )
            return self._run_direct(command, workdir)
        except Exception as e:
            result.stderr = str(e)

        result.duration_seconds = time.time() - start
        return result

    def _run_direct(self, command: str, workdir: str | Path) -> SandboxResult:
        """Fallback: run tests directly on host when no container runtime."""
        logger.info("Sandbox: Running directly on host (no container runtime)")
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(workdir),
            )
            return SandboxResult(
                passed=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                commands_run=[command],
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(stderr="Timed out (300s)", commands_run=[command])
        except Exception as e:
            return SandboxResult(stderr=str(e), commands_run=[command])

    def run_full_test_suite(self, workdir: str | Path = ".") -> SandboxResult:
        """Run the full test suite: lint → type → test.

        Args:
            workdir: Project directory.

        Returns:
            SandboxResult with combined output.
        """
        commands = [
            "python3 -m ruff check src/ tests/",
            "python3 -m mypy src/",
            "python3 -m pytest tests/ -q --tb=short --cov=src/ --cov-fail-under=10",
        ]
        combined = SandboxResult()

        for cmd in commands:
            logger.info("Sandbox: Running '%s'", cmd)
            result = self.run_tests(cmd, workdir)
            combined.stdout += f"$ {cmd}\n{result.stdout}\n"
            combined.stderr += result.stderr
            if not result.passed:
                combined.passed = False
                combined.exit_code = result.exit_code
                combined.commands_run.append(cmd)
                return combined
            combined.commands_run.append(cmd)

        combined.passed = True
        combined.exit_code = 0
        return combined

    def get_stderr_for_patching(
        self, result: SandboxResult, max_chars: int = 4000
    ) -> str:
        """Extract stderr for injection into model context.

        Args:
            result: SandboxResult from test execution.
            max_chars: Max characters to return.

        Returns:
            Truncated stderr suitable for context injection.
        """
        text = result.stderr or result.stdout
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... [truncated]"
        return text
