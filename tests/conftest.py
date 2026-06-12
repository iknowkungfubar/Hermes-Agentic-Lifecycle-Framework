"""Shared test fixtures and configuration for HALF.

Factory fixtures for creating test objects with overridable defaults.
Each test gets isolated state via tmp_path.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_half_home(tmp_path: Path) -> None:
    """Each test gets its own HALF_HOME, preventing cross-test pollution."""
    os.environ["HALF_HOME"] = str(tmp_path / ".hale")
    (tmp_path / ".hale").mkdir(parents=True, exist_ok=True)
    yield
    os.environ.pop("HALF_HOME", None)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with a minimal structure."""
    project = tmp_path / "test-project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "tests").mkdir()
    return project


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set common test environment variables."""
    monkeypatch.setenv("HALF_DB_PASSWORD", "test-secret")
    monkeypatch.setenv("HALF_LMSTUDIO_URL", "http://test:1234/v1")
