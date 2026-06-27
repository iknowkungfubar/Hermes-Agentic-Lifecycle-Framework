"""Integration tests for modules needing infrastructure: git_worktree, env_bootstrap, reflection_loop, prewarm, sandbox, webhooks, psm."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest


def _init_git_repo(path: Path) -> None:
    """Initialize a minimal git repo at path."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Tester"], cwd=str(path), capture_output=True
    )
    (path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=str(path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(path), capture_output=True)


class TestGitWorktreeIntegration:
    def test_create_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_git_repo(Path(tmp))
            from half.git_worktree import GitWorktreeManager

            mgr = GitWorktreeManager(repo_path=tmp)
            assert mgr.list_sessions() == []
            session = mgr.create_worktree("test-agent", "test/integration")
            assert session.worktree_path.exists()
            assert session in mgr.list_sessions()
            mgr.remove_worktree(session.session_id)


class TestEnvBootstrapIntegration:
    def test_capture_with_real_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_git_repo(Path(tmp))
            (Path(tmp) / "src").mkdir()
            (Path(tmp) / "src" / "main.py").write_text("def main(): return 42")
            from half.env_bootstrap import EnvironmentBootstrapper

            boot = EnvironmentBootstrapper(root_path=tmp)
            snap = boot.capture_snapshot("test task", "test-proj")
            assert snap.project_name == "test-proj"
            assert snap.task == "test task"
            assert len(snap.recent_git_history) > 0
            assert "src" in snap.directory_tree
            prompt = boot.build_bootstrap_prompt(snap)
            assert "test-proj" in prompt


class TestReflectionLoopIntegration:
    def test_run_with_git_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            _init_git_repo(Path(tmp))
            (Path(tmp) / ".harness").mkdir()
            (Path(tmp) / ".harness" / "agents.md").write_text("# Rules\n")
            from half.reflection_loop import ReflectionLoop

            loop = ReflectionLoop(repo_path=tmp)
            report = loop.run()
            assert isinstance(report.findings, list)
            assert isinstance(report.summary, str)


class TestPrewarmIntegration:
    def test_warm_container_create(self):
        from half.prewarm import PreWarmDeployment, WarmContainer

        pw = PreWarmDeployment()
        wc = WarmContainer(name="test-svc", image="test:latest")
        assert wc.name == "test-svc"
        assert wc.status == "warming"
        pw._warm_containers["test-svc"] = wc
        assert len(pw._warm_containers) == 1


class TestSandboxIntegration:
    def test_execution_sandbox_create(self):
        from half.sandbox import ExecutionSandbox

        try:
            sandbox = ExecutionSandbox()
            assert sandbox is not None
        except (FileNotFoundError, RuntimeError):
            pass  # Expected if no container runtime


class TestPSMIntegration:
    def test_discover_with_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            skills_dir.mkdir()
            (skills_dir / "test-skill.md").write_text(
                "---\nname: test\nversion: 1.0\n---\n# Test Skill"
            )
            from half.psm import PSMManager

            mgr = PSMManager(skills_dir=skills_dir)
            skills = mgr.discover()
            assert len(skills) >= 1


class TestHalfSidecarIntegration:
    def test_cmd_status(self):
        from half.half_sidecar import (
            cmd_gate_check,
            cmd_generate_mrp,
            cmd_run_phase,
            cmd_status,
        )

        s = cmd_status()
        assert isinstance(s, dict)
        assert cmd_generate_mrp() is not None
        assert cmd_gate_check("phase-1") is not None
        r = cmd_run_phase("phase-1")
        assert isinstance(r, dict)
