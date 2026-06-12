"""Contract tests for Reversibility Gate — tests pure classification logic."""

from half.reversibility_gate import ReversibilityGate


class TestReversibilityClassification:
    """Tests that the gate correctly classifies tasks by risk level."""

    def test_high_reversibility_readme_typo(self):
        gate = ReversibilityGate()
        d = gate.classify("T1", "Fix typo in README documentation")
        assert d.level.value == "high"
        assert d.requires_human is False

    def test_low_reversibility_auth(self):
        gate = ReversibilityGate()
        d = gate.classify("T2", "Add OAuth2 authentication to login endpoint")
        assert d.level.value == "low"
        assert d.requires_human is True

    def test_critical_security_cve(self):
        gate = ReversibilityGate()
        d = gate.classify("T3", "Patch CVE-2026-1234 in SSL certificate validation")
        assert d.level.value == "critical"

    def test_medium_feature_add(self):
        gate = ReversibilityGate()
        d = gate.classify("T4", "Add new analytics dashboard feature")
        assert d.level.value == "medium"

    def test_high_reversibility_css_change(self):
        gate = ReversibilityGate()
        d = gate.classify("T5", "Update CSS styles for login page")
        assert d.level.value == "high"

    def test_default_medium_no_keywords(self):
        gate = ReversibilityGate()
        d = gate.classify("T6", "Random uncategorized change")
        assert d.level.value == "medium"
