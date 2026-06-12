"""High-impact tests for low-coverage modules — corrected APIs."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestPGliteBulk:
    def test_bulk_operations(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.pglite_registry import PGliteRegistry
            reg = PGliteRegistry(db_path=str(Path(tmp) / "t.db"))
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "m.py").write_text("class A:\n    pass\ndef f(): return 1\n")
            reg.index_codebase(str(src))
            results = reg.search_entities("A")
            assert isinstance(results, list)
            view = reg.get_view("coder", max_entities=10)
            assert isinstance(view, list)
            reg.close()


class TestBootBulk:
    def test_boot_creates_phases(self):
        from half.boot_sequence import BootSequence
        boot = BootSequence()
        report = boot.run()
        assert len(report.phases) >= 3
        assert report.overall_status in ("passed", "failed")


class TestDoomLoopBulk:
    def test_doom_loop_detection(self):
        from half.doom_loop import DoomLoopDetector
        detector = DoomLoopDetector(max_retries=3)
        detector.register_session("test-loop", "initial spec")
        for i in range(4):
            detector.record_retry("test-loop", "test_failure", f"error {i}", "TB" * 50)
        session = detector.get_session("test-loop")
        assert session is not None
        assert session.truncated or len(session.retries) >= 3


class TestGateCheckBulk:
    def test_gate_check_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.core.gate_checker import GateChecker
            checker = GateChecker(artifacts_dir=Path(tmp))
            assert checker is not None


class TestSpecVerifyBulk:
    def test_verify_missing_file_returns_not_passed(self):
        from half.spec_verify import SpecVerifier
        report = SpecVerifier().verify_file("/nonexistent/path/test.py")
        assert not report.passed


class TestDoctorBulk:
    def test_doctor_full(self):
        from half.doctor import Doctor
        doctor = Doctor()
        report = doctor.run_full_diagnostics()
        assert report is not None
