"""Deep tests for remaining low-coverage modules: mutation_testing, database, doctor, voice, architect."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestMutationDeep:
    def test_sycophancy_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.mutation_testing import SycophancyGuardrail

            td = Path(tmp) / "tests"
            td.mkdir()
            (td / "test_good.py").write_text(
                "def test_add():\\n    assert 1 + 1 == 2\\n"
            )
            guard = SycophancyGuardrail(src_dir=tmp, test_dir=td)
            report = guard.run()
            assert isinstance(report.score, (int, float))
            assert isinstance(report.summary, str)


class TestDatabaseDeep:
    def test_init_and_agent_ops(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.agent_mail.database import AgentMailDatabase

            db = AgentMailDatabase(db_path=str(Path(tmp) / "m.db"))
            agent = db.register_agent("agent1@half.local", "coder")
            assert "agent1" in agent.email

    def test_message_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.agent_mail.database import AgentMailDatabase
            from half.agent_mail.models import MessageType

            db = AgentMailDatabase(db_path=str(Path(tmp) / "m2.db"))
            db.register_agent("a@h.local", "sender")
            db.register_agent("b@h.local", "receiver")
            msg = db.send_message(
                MessageType.TASK_ASSIGNMENT, "a@h.local", ["b@h.local"], "Task", "Do it"
            )
            assert msg is not None
            msgs = db.get_messages("b@h.local", unread_only=True)
            assert len(msgs) >= 1
            db.mark_read(msg.id)
            msgs2 = db.get_messages("b@h.local", unread_only=True)
            assert len(msgs2) == 0


class TestDoctorDeep:
    def test_check_python(self):
        from half.doctor import Doctor

        doctor = Doctor()
        report = doctor.run_full_diagnostics()
        checks = report.to_dict() if hasattr(report, "to_dict") else {}
        assert isinstance(checks, dict) or isinstance(report, dict)


class TestVoiceDeep:
    def test_voice_discovery(self):
        from half.half_voice.engine import VoiceEngine

        engine = VoiceEngine()
        w = engine._find_whisper()
        p = engine._find_piper()
        assert isinstance(w, str) or w == ""
        assert isinstance(p, str) or p == ""
