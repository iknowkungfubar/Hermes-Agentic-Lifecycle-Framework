"""Integration test fixtures — starts sidecar, creates test artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SIDECAR_PORT = 9721
SIDECAR_URL = f"http://127.0.0.1:{SIDECAR_PORT}"


def _wait_for_sidecar(timeout: int = 20) -> bool:
    """Wait for the sidecar HTTP server to be ready."""
    for _ in range(timeout * 2):
        try:
            r = urllib.request.urlopen(f"{SIDECAR_URL}/api/status", timeout=1)
            if r.status == 200:
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def sidecar_url() -> str:
    """Return the sidecar URL if running, skip otherwise."""
    if not _wait_for_sidecar(timeout=3):
        pytest.skip("Sidecar not running — start with: python -m half.http_sidecar")
    return SIDECAR_URL


@pytest.fixture
def test_audio_file() -> str:
    """Create a temporary WAV file for voice tests."""
    import struct
    import tempfile
    import wave

    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    f.close()
    with wave.open(f.name, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<" + "h" * 16000, *[0] * 16000))
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with history."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(repo), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "ci@test.com"],
        cwd=str(repo),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "CI"], cwd=str(repo), capture_output=True
    )
    (repo / "README.md").write_text("# Test")
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("def main(): return 42")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_main.py").write_text("def test_main(): assert True")
    (repo / ".harness").mkdir()
    (repo / ".harness" / "agents.md").write_text("# Rules\nKeep it simple.")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Initial commit"],
        cwd=str(repo),
        capture_output=True,
    )
    (repo / "src" / "utils.py").write_text("def util(): return 'hello'")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Add utils"], cwd=str(repo), capture_output=True
    )
    return repo


@pytest.fixture
def test_noslop_tree(tmp_path: Path) -> Path:
    """Create a multi-directory file tree for No-Slop indexing tests."""
    root = tmp_path / "noslop"
    for d in ["src/a", "src/b", "src/a/sub", "docs"]:
        (root / d).mkdir(parents=True)
    (root / "src/a/x.py").write_text("import os\ndef get_path(): return os.getcwd()\n")
    (root / "src/b/y.py").write_text("class Helper:\n    def help(self): return 42\n")
    (root / "src/a/sub/z.py").write_text("X = 1\ndef f(): return X\n")
    (root / "docs/index.md").write_text("# Docs\nReference.")
    return root
