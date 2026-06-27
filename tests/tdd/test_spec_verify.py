"""RED phase: Failing tests for SpecVerifier.

Test must fail first — proves they test real behavior.
"""

from pathlib import Path

import pytest


class TestSpecVerifier:
    """Tests for Spec-Driven Verification."""

    def test_verify_clean_file_passes(self, tmp_path: Path) -> None:
        """A file with valid Python should pass verification."""
        from half.spec_verify import SpecVerifier

        f = tmp_path / "clean.py"
        f.write_text("def foo() -> int:\n    return 42\n")
        report = SpecVerifier().verify_file(f)
        assert report.passed, f"Clean file should pass, got issues: {report.issues}"

    def test_verify_missing_file_fails(self) -> None:
        """A non-existent file should not pass verification."""
        from half.spec_verify import SpecVerifier

        report = SpecVerifier().verify_file("/nonexistent/test_foo.py")
        assert not report.passed

    def test_verify_dangerous_subprocess_call(self, tmp_path: Path) -> None:
        """A file calling subprocess.call should be flagged."""
        from half.spec_verify import SpecVerifier

        f = tmp_path / "unsafe.py"
        f.write_text("import subprocess\nsubprocess.call(['rm', '-rf', '/'])\n")
        report = SpecVerifier().verify_file(f)
        assert not report.passed
        assert any("Dangerous" in i.message for i in report.issues)

    def test_verify_empty_file_passes(self, tmp_path: Path) -> None:
        """An empty Python file should still pass verification."""
        from half.spec_verify import SpecVerifier

        f = tmp_path / "empty.py"
        f.write_text("")
        report = SpecVerifier().verify_file(f)
        assert report.passed
