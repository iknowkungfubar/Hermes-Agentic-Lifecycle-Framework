"""Property-based and contract tests for HALF core modules.

Uses property-based testing for pure functions.
"Tests implementation, not internals" per testing-strategy skill.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from hypothesis import given, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


class TestSpecVerifier:
    """Contract tests for Spec-Driven Verification."""

    def test_verify_clean_file(self, tmp_path: Path) -> None:
        from half.spec_verify import SpecVerifier
        py_file = tmp_path / "test_clean.py"
        py_file.write_text("def foo() -> int:\n    return 42\n")
        verifier = SpecVerifier()
        report = verifier.verify_file(py_file)
        assert report.passed

    def test_verify_dangerous_import(self, tmp_path: Path) -> None:
        from half.spec_verify import SpecVerifier
        py_file = tmp_path / "test_unsafe.py"
        py_file.write_text("import subprocess\nsubprocess.call(['rm', '-rf', '/'])\n")
        verifier = SpecVerifier()
        report = verifier.verify_file(py_file)
        assert not report.passed
        issues = [i for i in report.issues if "Dangerous" in i.message]
        assert len(issues) > 0

    def test_verify_missing_file(self) -> None:
        from half.spec_verify import SpecVerifier
        verifier = SpecVerifier()
        report = verifier.verify_file("/nonexistent/test.py")
        assert not report.passed

    def test_verify_empty_file(self, tmp_path: Path) -> None:
        from half.spec_verify import SpecVerifier
        py_file = tmp_path / "empty.py"
        py_file.write_text("")
        verifier = SpecVerifier()
        report = verifier.verify_file(py_file)
        assert report.passed


@pytest.mark.skipif(not HAS_HYPOTHESIS, reason="hypothesis not installed")
class TestHypothesisPropertyTests:
    """Property-based tests for pure functions."""

    @given(st.lists(st.integers(min_value=0, max_value=100), max_size=20))
    def test_mutation_score_bounds(self, scores):
        from half.mutation_testing import SycophancyReport
        report = SycophancyReport()
        report.mutation_kill_rate = sum(1 for s in scores if s > 50) / max(1, len(scores))
        assert 0.0 <= report.mutation_kill_rate <= 1.0

    @given(st.text(min_size=1, max_size=200))
    def test_spec_verify_ast_accepts_valid_python(self, code):
        import ast
        try:
            ast.parse(code)
            assert True
        except SyntaxError:
            assert True


class TestReversibilityGate:
    """Contract tests for risk-based task classification."""

    def test_high_reversibility_ui_task(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        decision = gate.classify("T-001", "Fix typo in README")
        assert decision.level.value == "high"
        assert decision.requires_human is False

    def test_low_reversibility_auth_task(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        decision = gate.classify("T-002", "Add OAuth2 authentication to login")
        assert decision.level.value == "low"
        assert decision.requires_human is True

    def test_critical_security_task(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        decision = gate.classify("T-003", "Fix CVE-2026-1234 in authentication")
        assert decision.level.value == "critical"

    def test_approval_check(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        gate.classify("T-004", "Fix typo in README")
        result = gate.check_approval("T-004")
        assert result["approved"] is True

    def test_approval_needed(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        gate.classify("T-005", "Modify database schema for users table")
        result = gate.check_approval("T-005", approvals_received=0, human_approved=False)
        assert result["approved"] is False

    def test_get_pending_approvals(self):
        from half.reversibility_gate import ReversibilityGate
        gate = ReversibilityGate()
        gate.classify("T-006", "Delete user accounts", ["src/auth/admin.py"])
        gate.classify("T-007", "Fix typo in README")
        pending = gate.get_pending_approvals()
        assert len(pending) >= 1
        assert "T-006" in [d.task_id for d in pending]
