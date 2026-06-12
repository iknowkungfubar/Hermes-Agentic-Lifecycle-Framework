"""End-to-end pipeline integration test — full lifecycle from init to MRP."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


class TestFullPipeline:
    """Full HALF pipeline: init → status → gate-check → run-phase → generate-mrp."""

    def test_full_lifecycle(self, tmp_path):
        env = {**os.environ, "PYTHONPATH": "."}
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Step 1: init
        r = subprocess.run(
            [sys.executable, "-m", "half.__main__", "init",
             "--project", "test-project", "--mode", "full", "--dir", str(project_dir)],
            capture_output=True, text=True, timeout=30, env=env,
        )
        assert r.returncode == 0, f"init failed: {r.stderr}"

        # Step 2: status
        r = subprocess.run(
            [sys.executable, "-m", "half.__main__", "status"],
            capture_output=True, text=True, timeout=10, env=env,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert isinstance(data, dict)

        # Step 3: gate-check phase-1
        r = subprocess.run(
            [sys.executable, "-m", "half.__main__", "gate-check", "phase-1"],
            capture_output=True, text=True, timeout=10, env=env,
        )
        assert r.returncode == 0

        # Step 4: run-phase phase-1
        r = subprocess.run(
            [sys.executable, "-m", "half.__main__", "run-phase", "phase-1"],
            capture_output=True, text=True, timeout=30, env=env,
        )
        assert r.returncode == 0

        # Step 5: generate-mrp
        r = subprocess.run(
            [sys.executable, "-m", "half.__main__", "generate-mrp"],
            capture_output=True, text=True, timeout=30, env=env,
        )
        assert r.returncode == 0
