"""Deep coverage for worst-offending modules — target 80%."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestPGliteDeep:
    def test_full_registry_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.pglite_registry import AGENT_VIEWS, PGliteRegistry

            db = str(Path(tmp) / "p.db")
            reg = PGliteRegistry(db_path=db)

            # Index files
            (Path(tmp) / "a.py").write_text(
                "import os\nX=1\ndef f():return X\nclass C:pass\n"
            )
            reg.index_codebase(tmp)

            # Search
            r = reg.search_entities("f", entity_type="function")
            assert isinstance(r, list)

            # Views
            for role in ["coder", "dba", "security"]:
                v = reg.get_view(role)
                assert isinstance(v, list)

            # Preferences
            reg.set_preference("k1", "v1")
            assert reg.get_preference("k1") == "v1"
            reg.set_preference("k2", "v2")
            prefs = reg.get_all_preferences()
            assert "k1" in prefs

            # Subscriptions
            reg.subscribe("auditor", ["class"])
            subs = reg.get_subscription("auditor")
            assert "class" in subs

            # Stats
            st = reg.get_stats()
            assert "entities" in st
            reg.close()


class TestBootDeep:
    def test_phase1_hardware_checks(self):
        from half.boot_sequence import BootSequence

        boot = BootSequence()
        report = boot.run()
        phase1 = report.phases[0]
        assert phase1.phase == 1
        assert len(phase1.checks) > 0

    def test_report_string(self):
        from half.boot_sequence import BootSequence

        boot = BootSequence()
        boot.run()
        output = boot.print_report()
        assert "Boot" in output or "HALF" in output


class TestGateCheckerDeep:
    def test_phase1_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.core.gate_checker import GateCheck, GateChecker

            artifacts = Path(tmp)
            (artifacts / "phase-1").mkdir(parents=True)
            (artifacts / "phase-1" / "01-REQUIREMENTS.md").write_text("# Reqs\n")
            (artifacts / "phase-1" / "02-SPECIFICATION.md").write_text("# Spec\n")
            gc = GateChecker(artifacts_dir=artifacts)
            results = gc.check_phase_1()
            assert isinstance(results, list)
            for r in results:
                assert "passed" in r

    def test_has_blocking_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.core.gate_checker import GateChecker

            gc = GateChecker(artifacts_dir=Path(tmp))
            assert (
                gc.has_blocking_failures([{"passed": True, "blocking": True}]) is False
            )
            assert (
                gc.has_blocking_failures([{"passed": False, "blocking": True}]) is True
            )

    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.core.gate_checker import GateChecker

            gc = GateChecker(artifacts_dir=Path(tmp))
            s = gc.summary(
                [
                    {"passed": True, "blocking": False},
                    {"passed": False, "blocking": True},
                ]
            )
            assert isinstance(s, str)


class TestDatabaseDeep:
    def test_db_helpers(self):
        from half.agent_mail.database import cleanup_db, get_db

        cleanup_db()
        db = get_db()
        assert db is not None


class TestDoomLoopDeep:
    def test_doom_loop_analysis(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector(max_retries=3)
        detector.register_session("dl-test", "spec")
        # Trigger doom loop with 3+ same error type
        for i in range(3):
            detector.record_retry("dl-test", "timeout", f"timeout #{i}", "TB" * 100)
        session = detector.get_session("dl-test")
        assert session is not None
        assert session.truncated

    def test_growing_traceback(self):
        from half.doom_loop import DoomLoopDetector

        detector = DoomLoopDetector(max_retries=5)
        detector.register_session("dl-tb", "spec")
        tb = "x"
        for i in range(5):
            tb = tb * 10  # Growing traceback
            detector.record_retry("dl-tb", "error", f"err {i}", tb)
        session = detector.get_session("dl-tb")
        assert session is not None


class TestSpecVerifyDeep:
    def test_verify_missing_file(self):
        from half.spec_verify import SpecVerifier

        r = SpecVerifier().verify_file("/nonexistent/test.py")
        assert not r.passed

    def test_verify_empty_file(self, tmp_path):
        from half.spec_verify import SpecVerifier

        f = tmp_path / "e.py"
        f.write_text("")
        r = SpecVerifier().verify_file(f)
        assert r.passed

    def test_verify_dangerous(self, tmp_path):
        from half.spec_verify import SpecVerifier

        f = tmp_path / "d.py"
        f.write_text("import subprocess\nsubprocess.call(['rm'])\n")
        r = SpecVerifier().verify_file(f)
        assert not r.passed
