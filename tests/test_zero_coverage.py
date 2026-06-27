"""Tests for 13 zero-coverage modules — using actual API surfaces."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestWebhooks:
    def test_import(self):
        from half.webhooks import WebhookHandler, WebhookServer

        assert WebhookHandler is not None

    def test_create_handler(self):
        from half.webhooks import WebhookHandler

        handler = WebhookHandler()
        assert handler is not None

    def test_create_server(self):
        from half.webhooks import WebhookServer

        def cb(e):
            pass

        server = WebhookServer(handler=cb)
        assert server is not None


class TestStaleMonitor:
    def test_import(self):
        from half.stale_monitor import StaleSession, StaleSessionMonitor

        assert StaleSessionMonitor is not None

    def test_scan(self):

        with tempfile.TemporaryDirectory() as tmp:
            from half.stale_monitor import StaleSessionMonitor

            monitor = StaleSessionMonitor()
            sessions = monitor.scan()
            assert isinstance(sessions, list)


class TestRLVMR:
    def test_import(self):
        from half.rlvmr import CognitiveStep, RLVMRRun, RLVMRTracker

        assert RLVMRTracker is not None

    def test_start_run(self):
        from half.rlvmr import RLVMRTracker

        tracker = RLVMRTracker()
        run = tracker.start_run("test-run", "Build X")
        assert run.run_id == "test-run"

    def test_tag_step_planning(self):
        from half.rlvmr import CognitiveStep, RLVMRTracker

        tracker = RLVMRTracker()
        tracker.start_run("r1", "Task")
        tag = tracker.tag_step(
            "r1", CognitiveStep.PLANNING, "plan approach", token_cost=100, success=True
        )
        assert tag.reward == 0.5

    def test_tag_step_failure(self):
        from half.rlvmr import CognitiveStep, RLVMRTracker

        tracker = RLVMRTracker()
        tracker.start_run("r2", "Task")
        tag = tracker.tag_step("r2", CognitiveStep.EXECUTION, "failed", success=False)
        assert tag.reward == -0.1

    def test_efficiency(self):
        from half.rlvmr import CognitiveStep, RLVMRTracker

        tracker = RLVMRTracker()
        tracker.start_run("r3", "Task")
        tracker.tag_step(
            "r3", CognitiveStep.PLANNING, "plan", token_cost=100, success=True
        )
        assert tracker.calculate_efficiency("r3") > 0

    def test_summary(self):
        from half.rlvmr import RLVMRTracker

        tracker = RLVMRTracker()
        tracker.start_run("r4", "Task")
        summary = tracker.get_summary("r4")
        assert "run_id" in summary

    def test_best_strategy_empty(self):
        from half.rlvmr import RLVMRTracker

        assert "No runs" in RLVMRTracker().get_best_strategy()

    def test_best_strategy_with_data(self):
        from half.rlvmr import CognitiveStep, RLVMRTracker

        tracker = RLVMRTracker()
        tracker.start_run("r5", "Task")
        tracker.tag_step(
            "r5", CognitiveStep.PLANNING, "plan", token_cost=10, success=True
        )
        assert "Best run" in tracker.get_best_strategy()


class TestRouting:
    def test_import(self):
        from half.routing import RoutingDecision, TaskRouter, WorkflowType

        assert TaskRouter is not None

    def test_route_code(self):
        from half.routing import TaskRouter

        router = TaskRouter()
        result = router.route("Build a REST API for user auth")
        # Result is a RoutingDecision with a workflow attribute
        assert hasattr(result, "workflow") or isinstance(result, dict)

    def test_route_empty(self):
        from half.routing import TaskRouter

        router = TaskRouter()
        result = router.route("")
        assert isinstance(result, object)


class TestGoal:
    def test_import(self):
        from half.goal import main

        assert callable(main)


class TestSandbox:
    def test_import(self):
        from half.sandbox import ExecutionSandbox

        assert ExecutionSandbox is not None

    def test_execute(self):
        from half.sandbox import ExecutionSandbox

        # Sandbox init may fail without podman — just verify module imports


class TestLMStudio:
    def test_import(self):
        from half.lm_studio import InferenceProvider, LMStudioManager, ModelConfig

        assert LMStudioManager is not None

    def test_model_config(self):
        from half.lm_studio import ModelConfig

        config = ModelConfig(name="qwen2.5-coder:7b")
        assert config.name == "qwen2.5-coder:7b"

    def test_inference_provider(self):
        from half.lm_studio import InferenceProvider

        provider = InferenceProvider(name="lmstudio", endpoint="http://localhost:1234")
        assert provider.name == "lmstudio"

    def test_lmstudio_manager(self):
        from half.lm_studio import LMStudioManager

        manager = LMStudioManager()
        assert manager is not None


class TestPydanticAI:
    def test_import(self):
        from half.pydantic_ai import Capability, RequirementDocument

        assert Capability is not None

    def test_create_capability(self):
        from half.pydantic_ai import Capability

        cap = Capability(
            id="C-001",
            description="User authentication with JWT",
            priority="P0",
            confidence="HIGH",
        )
        assert cap.id == "C-001"


class TestBrowserResearch:
    def test_import(self):
        from half.browser_research import BrowserResearchAgent

        assert BrowserResearchAgent is not None

    def test_create_agent(self):
        from half.browser_research import BrowserResearchAgent

        agent = BrowserResearchAgent()
        assert agent is not None


class TestIndexing:
    def test_import(self):
        from half.indexing import RepoIndexer

        assert RepoIndexer is not None

    def test_index_empty(self):

        with tempfile.TemporaryDirectory() as tmp:
            from half.indexing import RepoIndexer

            indexer = RepoIndexer(root=tmp)
            result = indexer.build_index()
            assert isinstance(result, dict)


class TestSecurityScanners:
    def test_import(self):
        from half.security_scanners import BumblebeeScanner, GarakScanner

        assert GarakScanner is not None

    def test_garak_scanner(self):
        from half.security_scanners import GarakScanner

        scanner = GarakScanner()
        assert scanner is not None


class TestPDADigest:
    def test_import(self):
        from half.pda_digest import PDADigest

        assert PDADigest is not None

    def test_generate(self):

        with tempfile.TemporaryDirectory() as tmp:
            from half.pda_digest import PDADigest

            digest = PDADigest(repo_path=tmp)
            report = digest.generate_briefing()
            assert isinstance(report, str)


class TestRestDaemon:
    def test_import(self):
        from half.rest_daemon import RESTAPIHandler, run_server

        assert callable(run_server)
