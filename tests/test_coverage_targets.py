"""Targeted coverage for highest-missed modules: nodes, gate_checker, pglite_registry, database, mutation, doctor, boot, doom_loop."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestGateChecker:
    def test_import(self):
        from half.core.gate_checker import GateCheck, GateChecker
        assert GateCheck is not None

    def test_create_gate(self):
        from half.core.gate_checker import GateCheck
        gate = GateCheck("G1", "Test gate", lambda: (True, "ok"))
        assert gate.gate_id == "G1"

    def test_run_gate_passes(self):
        from half.core.gate_checker import GateCheck
        gate = GateCheck("G2", "Passing gate", lambda: (True, "ok"))
        result = gate.run()
        assert result["passed"] is True

    def test_run_gate_fails(self):
        from half.core.gate_checker import GateCheck
        gate = GateCheck("G3", "Failing gate", lambda: (False, "nok"))
        result = gate.run()
        assert result["passed"] is False

    def test_run_gate_exception(self):
        from half.core.gate_checker import GateCheck
        def broken():
            raise ValueError("test error")
        gate = GateCheck("G4", "Broken gate", broken)
        result = gate.run()
        assert result["passed"] is False


class TestDoomLoop:
    def test_import(self):
        from half.doom_loop import DoomLoopDetector
        assert DoomLoopDetector is not None

    def test_register_session(self):
        from half.doom_loop import DoomLoopDetector
        detector = DoomLoopDetector()
        detector.register_session("s1", "spec")
        session = detector.get_session("s1")
        assert session is not None
        assert session.initial_spec == "spec"

    def test_retry_record(self):
        from half.doom_loop import DoomLoopDetector
        detector = DoomLoopDetector(max_retries=5)
        detector.register_session("s2", "spec")
        result = detector.record_retry("s2", "test_failure", "Assert failed", "Trace...")
        assert "doom_loop_detected" in result


class TestBootSequence:
    def test_import(self):
        from half.boot_sequence import BootSequence, BootPhase
        assert BootSequence is not None

    def test_run_boot(self):
        from half.boot_sequence import BootSequence
        boot = BootSequence()
        report = boot.run()
        assert len(report.phases) == 4


class TestDoctor:
    def test_import(self):
        from half.doctor import Doctor, DoctorReport
        assert Doctor is not None

    def test_run_diagnostics(self):
        from half.doctor import Doctor
        doctor = Doctor()
        report = doctor.run_full_diagnostics()
        assert isinstance(report, dict) or hasattr(report, 'checks')


class TestMutationTesting:
    def test_import(self):
        from half.mutation_testing import SycophancyGuardrail
        assert SycophancyGuardrail is not None

    def test_run_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / "tests"
            test_dir.mkdir()
            (test_dir / "test_x.py").write_text("def test_ok():\\n    assert 1 + 1 == 2\\n")
            from half.mutation_testing import SycophancyGuardrail
            guard = SycophancyGuardrail(src_dir=tmp, test_dir=test_dir)
            report = guard.run()
            assert report.score <= 100


class TestPGliteRegistryDeep:
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.pglite_registry import PGliteRegistry
            db_path = str(Path(tmp) / "reg.db")
            reg = PGliteRegistry(db_path=db_path)
            assert reg.get_stats() is not None
            reg.close()


class TestAgentMailDB:
    def test_import(self):
        from half.agent_mail.database import AgentMailDatabase
        assert AgentMailDatabase is not None

    def test_init(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            from half.agent_mail.database import AgentMailDatabase
            db = AgentMailDatabase(db_path=str(Path(tmp) / "mail.db"))
            assert db is not None


class TestRuntimeNodes:
    def test_import_node_funcs(self):
        from half.runtime.nodes import (
            phase_1_discovery, phase_1_specification, phase_1_architecture,
            phase_1_gate, phase_2_scaffold
        )
        assert callable(phase_1_discovery)

    def test_phase_1_discovery(self):
        from half.runtime.nodes import phase_1_discovery
        result = phase_1_discovery({"task_description": "test"})
        assert isinstance(result, dict)
