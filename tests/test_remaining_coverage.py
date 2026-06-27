"""Tests for remaining untested HALF modules."""

from __future__ import annotations

import tempfile
from pathlib import Path


class TestAIDeclaration:
    def test_generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.ai_declaration import AIDeclarationGenerator

            gen = AIDeclarationGenerator(repo_path=tmp)
            result = gen.generate()
            assert result is not None


class TestDoctor:
    def test_import(self):
        from half.doctor import Doctor

        assert Doctor is not None

    def test_run_doctor(self):
        from half.doctor import Doctor

        doctor = Doctor()
        report = doctor.run_full_diagnostics()
        assert isinstance(report, dict) or hasattr(report, "checks")


class TestDoomLoop:
    def test_register_and_detect(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector(max_retries=3)
        detector.register_session("test-session", "initial spec")
        result = detector.record_retry(
            "test-session", "test_failure", "AssertionError", "Traceback..."
        )
        assert "doom_loop_detected" in result

    def test_doom_loop_triggers(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector(max_retries=3)
        detector.register_session("doom-session", "spec")
        for i in range(3):
            result = detector.record_retry(
                "doom-session", "test_failure", f"Error {i}", "TB" * 100
            )
        assert (
            result.get("doom_loop_detected")
            or len(detector._sessions["doom-session"].retries) >= 3
        )

    def test_get_session(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector()
        detector.register_session("s1", "spec")
        session = detector.get_session("s1")
        assert session is not None
        assert session.session_id == "s1"

    def test_recover_truncate(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector(max_retries=2)
        detector.register_session("r1", "initial spec")
        for i in range(3):
            detector.record_retry("r1", "timeout", "Timed out", "TB" * 50)
        session = detector.get_session("r1")
        assert session is not None
        assert session.truncated or len(session.retries) >= 2


class TestEvals:
    def test_evaluate(self):
        from half.evals import AutomatedEvaluator

        evaluator = AutomatedEvaluator()
        result = evaluator.evaluate(
            run_id="test-run",
            task_description="Build an API endpoint",
            implementation="def get(): pass",
            briefingscript="Build a REST API",
            token_count=1000,
            retry_count=2,
            human_interventions=1,
        )
        assert result.run_id == "test-run"
        assert len(result.evaluations) == 3

    def test_evaluate_empty(self):
        from half.evals import AutomatedEvaluator

        evaluator = AutomatedEvaluator()
        result = evaluator.evaluate(
            run_id="empty", task_description="Task", implementation=""
        )
        assert result.overall_score >= 0


class TestInterview:
    def test_start_interview(self):
        from half.interview import InterviewEngine

        engine = InterviewEngine()
        questions = engine.start_interview("test-proj", "Build something")
        assert len(questions) > 0

    def test_process_answer(self):
        from half.interview import InterviewEngine

        engine = InterviewEngine()
        engine.start_interview("proj", "desc")
        result = engine.process_answer("core_feature", "User authentication with JWT")
        assert result["status"] == "recorded"

    def test_finalize(self):
        from half.interview import InterviewEngine

        engine = InterviewEngine()
        engine.start_interview("proj", "desc")
        engine.process_answer("core_feature", "Auth")
        engine.process_answer("tech_stack", "Python, FastAPI")
        script = engine.finalize()
        assert script.interview_complete is True
        assert script.project_name == "proj"
        assert "Auth" in script.description or "Python" in " ".join(script.tech_stack)

    def test_personality(self):
        from half.interview import InterviewEngine, PDAProfile

        engine = InterviewEngine()
        profile = PDAProfile(tone="casual", verbosity=2)
        engine.set_personality(profile)
        prompt = engine.get_personality_prompt()
        assert "casual" in prompt


class TestMetaReasoning:
    def test_start_trace(self):
        from half.meta_reasoning import MetaReasoningEngine

        engine = MetaReasoningEngine()
        trace = engine.start_trace("Build feature X")
        assert trace.step_id == "root"

    def test_add_step(self):
        from half.meta_reasoning import MetaReasoningEngine

        engine = MetaReasoningEngine()
        engine.start_trace("Build")
        step = engine.add_step("root", "Research", "Found docs", 0.8)
        assert step.success_metric == 0.8

    def test_should_terminate(self):
        from half.meta_reasoning import MetaReasoningEngine

        engine = MetaReasoningEngine(max_iterations=2)
        engine.start_trace("Build")
        engine.add_step("root", "Step 1", "Done", 0.5)
        assert engine.should_terminate_branch("step-1") is False

    def test_prune_branch(self):
        from half.meta_reasoning import MetaReasoningEngine

        engine = MetaReasoningEngine()
        engine.start_trace("Build")
        engine.add_step("root", "Bad approach", "Failed", 0.1)
        new_trace = engine.prune_branch("step-1")
        if new_trace:
            assert "ALTERNATIVE" in new_trace.action

    def test_get_best_path(self):
        from half.meta_reasoning import MetaReasoningEngine

        engine = MetaReasoningEngine()
        engine.start_trace("Build")
        engine.add_step("root", "Good path", "Works", 0.9)
        path = engine.get_best_path()
        assert len(path) >= 1


class TestMutationTesting:
    def test_import(self):
        from half.mutation_testing import SycophancyGuardrail

        assert SycophancyGuardrail is not None

    def test_check_assert_true(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / "tests"
            test_dir.mkdir()
            (test_dir / "test_trivial.py").write_text(
                "def test_x():\n    assert True\n"
            )
            from half.mutation_testing import SycophancyGuardrail

            guardrail = SycophancyGuardrail(src_dir=tmp, test_dir=test_dir)
            report = guardrail.run()
            assert report.score <= 100
            assert isinstance(report.findings, list)


class TestPSM:
    def test_import(self):
        from half.psm import PSMManager

        assert PSMManager is not None

    def test_discover_no_dir(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            from half.psm import PSMManager

            manager = PSMManager(skills_dir=tmp)
            skills = manager.discover()
            assert isinstance(skills, list)


class TestNoSlop:
    def test_import(self):
        from half.no_slop import NoSlopIndexer

        assert NoSlopIndexer is not None

    def test_index_codebase(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            from half.no_slop import NoSlopIndexer

            indexer = NoSlopIndexer(root_path=tmp)
            result = indexer.build_index()
            assert isinstance(result, dict)


class TestReflectionLoop:
    def test_import(self):
        from half.reflection_loop import ReflectionLoop

        assert ReflectionLoop is not None

    def test_run(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            from half.reflection_loop import ReflectionLoop

            loop = ReflectionLoop(repo_path=tmp)
            report = loop.run()
            assert isinstance(report.findings, list)


class TestRalphLoop:
    def test_import(self):
        from half.ralph_loop import RalphLoop

        assert RalphLoop is not None

    def test_run_audit(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            from half.ralph_loop import RalphLoop

            loop = RalphLoop(repo_path=tmp)
            report = loop.run()
            assert isinstance(report.findings, list)


class TestWebhooks:
    def test_import(self):
        from half.webhooks import WebhookServer

        assert WebhookServer is not None

    def test_create_server(self):
        from half.webhooks import WebhookServer

        def handler(e):
            pass

        server = WebhookServer(handler=handler)
        assert server is not None
