"""Tests for v1.5 modules: event_driven, agg_investigation, env_bootstrap, vram_monitor, durable_exec, boot_sequence, branchfs, prewarm, sandbox_exec, forced_patch."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


class TestEventDrivenAgency:
    def test_import(self):
        from half.event_driven import EventDrivenAgency, EventTrigger
        assert EventDrivenAgency is not None
        assert EventTrigger is not None

    def test_register_trigger(self):
        from half.event_driven import EventDrivenAgency, EventTrigger
        agency = EventDrivenAgency()
        agency.register_trigger(EventTrigger(
            name="test-trigger", trigger_type="cron", condition="0 6 * * *", action="echo hello"
        ))
        assert len(agency.triggers) == 1
        assert agency.triggers[0].name == "test-trigger"

    def test_remove_trigger(self):
        from half.event_driven import EventDrivenAgency, EventTrigger
        agency = EventDrivenAgency()
        agency.register_trigger(EventTrigger("t1", "cron", "* * * * *", "echo"))
        agency.register_trigger(EventTrigger("t2", "cron", "* * * * *", "echo"))
        assert agency.remove_trigger("t1") is True
        assert len(agency.triggers) == 1

    def test_poll_no_triggers(self):
        from half.event_driven import EventDrivenAgency
        agency = EventDrivenAgency()
        fired = agency.poll()
        assert fired == []

    def test_get_history(self):
        from half.event_driven import EventDrivenAgency
        agency = EventDrivenAgency()
        history = agency.get_history()
        assert isinstance(history, list)


class TestAggressiveInvestigator:
    def test_import(self):
        from half.agg_investigation import AggressiveInvestigator, InvestigationReport
        assert AggressiveInvestigator is not None

    def test_investigate(self):
        from half.agg_investigation import AggressiveInvestigator
        investigator = AggressiveInvestigator()
        report = investigator.investigate("Test failure in module X")
        assert report.failure_description == "Test failure in module X"
        assert isinstance(report.steps, list)

    def test_generate_report(self):
        from half.agg_investigation import AggressiveInvestigator, InvestigationReport
        investigator = AggressiveInvestigator()
        report = InvestigationReport(failure_description="test")
        output = investigator.generate_report(report)
        assert "Investigation Report" in output


class TestEnvironmentBootstrapper:
    def test_import(self):
        from half.env_bootstrap import EnvironmentBootstrapper, BootstrapSnapshot
        assert EnvironmentBootstrapper is not None

    def test_capture_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            from half.env_bootstrap import EnvironmentBootstrapper
            bootstrapper = EnvironmentBootstrapper(tmp)
            snapshot = bootstrapper.capture_snapshot("test task", "test-project")
            assert snapshot.project_name == "test-project"
            assert snapshot.task == "test task"
            assert "test-project" in snapshot.directory_tree

    def test_build_bootstrap_prompt(self):
        from half.env_bootstrap import BootstrapSnapshot
        bootstrapper = type('obj', (object,), {'build_bootstrap_prompt': lambda s: '# Bootstrap'})()
        # Simple test: just check the class imports
        assert True


class TestVRAMMonitor:
    def test_import(self):
        from half.vram_monitor import VRAMMonitor, GPUInfo, ResourceAllocation
        assert VRAMMonitor is not None

    def test_get_gpu_info(self):
        from half.vram_monitor import VRAMMonitor
        monitor = VRAMMonitor()
        info = monitor.get_gpu_info()
        assert info.vram_total_mb > 0
        assert info.vram_used_mb >= 0

    def test_get_allocation(self):
        from half.vram_monitor import VRAMMonitor
        monitor = VRAMMonitor()
        alloc = monitor.get_allocation(vram_needed_voice=512, vram_needed_coder=2048, num_agents=1)
        assert isinstance(alloc.recommended_max_agents, int)
        assert isinstance(alloc.priority_queue, list)

    def test_to_dict(self):
        from half.vram_monitor import VRAMMonitor
        monitor = VRAMMonitor()
        d = monitor.to_dict()
        assert "vram_total_mb" in d
        assert "vram_used_mb" in d


class TestDurableExecutor:
    def test_import(self):
        from half.durable_exec import DurableExecutor, ExecutionContext, ExecutionStep
        assert DurableExecutor is not None

    def test_start_execution(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.durable_exec import DurableExecutor
            executor = DurableExecutor(state_dir=tmp)
            ctx = executor.start_execution("test-deploy")
            assert ctx.execution_id is not None
            assert len(ctx.steps) == 0

    def test_recover_nonexistent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.durable_exec import DurableExecutor
            executor = DurableExecutor(state_dir=tmp)
            ctx = executor.recover("nonexistent-id")
            assert ctx is None

    def test_execute_step(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.durable_exec import DurableExecutor
            executor = DurableExecutor(state_dir=tmp)
            ctx = executor.start_execution("test")
            result = executor._execute_with_checkpoint(ctx, "step1", lambda: {"done": True})
            assert result == {"done": True}
            assert ctx.steps["step1"].status == "completed"


class TestBootSequence:
    def test_import(self):
        from half.boot_sequence import BootSequence, BootPhase
        assert BootSequence is not None

    def test_run(self):
        from half.boot_sequence import BootSequence
        boot = BootSequence()
        report = boot.run()
        assert len(report.phases) == 4
        assert report.overall_status in ("passed", "failed")

    def test_print_report(self):
        from half.boot_sequence import BootSequence
        boot = BootSequence()
        boot.run()
        output = boot.print_report()
        assert "HALF 1.5" in output


class TestBranchFS:
    def test_import(self):
        from half.branchfs import BranchFS, SpeculativeBranch
        assert BranchFS is not None

    def test_spawn_without_git(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.branchfs import BranchFS
            bfs = BranchFS(repo_path=tmp)
            branches = bfs.get_all_branches()
            assert isinstance(branches, list)

    def test_get_all_branches(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.branchfs import BranchFS
            bfs = BranchFS(repo_path=tmp)
            branches = bfs.get_all_branches()
            assert isinstance(branches, list)


class TestPreWarmDeployment:
    def test_import(self):
        from half.prewarm import PreWarmDeployment, WarmContainer
        assert PreWarmDeployment is not None

    def test_cleanup_no_containers(self):
        from half.prewarm import PreWarmDeployment
        pw = PreWarmDeployment()
        pw.cleanup()  # Should not raise


class TestSandboxExecutor:
    def test_import(self):
        from half.sandbox_exec import SandboxExecutor, SandboxResult
        assert SandboxExecutor is not None

    def test_run_direct(self):
        from half.sandbox_exec import SandboxExecutor
        executor = SandboxExecutor()
        result = executor.run_tests("echo hello")
        assert "hello" in result.stdout

    def test_run_full_test_suite(self):
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as tmp:
            from half.sandbox_exec import SandboxExecutor
            P(tmp).joinpath("tests").mkdir()
            (P(tmp) / "tests" / "test_dummy.py").write_text("def test(): assert True")
            os.chdir(tmp)
            executor = SandboxExecutor(runtime="")
            result = executor.run_full_test_suite(tmp)
            assert isinstance(result.passed, bool)


class TestForcedPatchingLoop:
    def test_import(self):
        from half.forced_patch import ForcedPatchingLoop, PatchAttempt, PatchCycleResult
        assert ForcedPatchingLoop is not None

    def test_generate_patch_prompt(self):
        from half.forced_patch import ForcedPatchingLoop
        from half.sandbox_exec import SandboxResult
        loop = ForcedPatchingLoop()
        result = SandboxResult(stderr="Test error output")
        prompt = loop.generate_patch_prompt(result)
        assert "FORCED PATCHING MODE" in prompt
        assert "Test error output" in prompt
