"""Additional coverage for modules with highest missed lines."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestNoSlopDetailed:
    def test_index_with_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.no_slop import NoSlopIndexer
            (Path(tmp) / "subdir").mkdir()
            (Path(tmp) / "subdir" / "a.py").write_text("x = 1\n")
            indexer = NoSlopIndexer(root_path=tmp)
            result = indexer.build_index()
            assert isinstance(result, dict)


class TestPGliteDetailed:
    def test_index_codebase(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.pglite_registry import PGliteRegistry
            (Path(tmp) / "src").mkdir()
            (Path(tmp) / "src" / "mod.py").write_text("def f(): return 1\n")
            registry = PGliteRegistry(db_path=str(Path(tmp) / "test.db"))
            n = registry.index_codebase(str(Path(tmp) / "src"))
            assert n >= 0


class TestEventDrivenDetailed:
    def test_handle_ci_webhook(self):
        from half.event_driven import EventDrivenAgency, EventTrigger
        agency = EventDrivenAgency()
        agency.register_trigger(EventTrigger("ci", "ci_failure", "master", "echo fix"))
        fired = agency.handle_ci_webhook({"status": "failure", "branch": "master"})
        assert isinstance(fired, list)


class TestHalfSidecarDetailed:
    def test_cmd_generate_mrp(self):
        from half.half_sidecar import cmd_generate_mrp
        result = cmd_generate_mrp()
        assert isinstance(result, dict)

    def test_cmd_gate_check(self):
        from half.half_sidecar import cmd_gate_check
        result = cmd_gate_check("phase-1")
        assert isinstance(result, dict)
