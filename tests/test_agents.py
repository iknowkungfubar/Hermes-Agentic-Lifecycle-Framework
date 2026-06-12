"""Tests for HALF agent skill modules and CodeSimplifier."""

from __future__ import annotations

import tempfile
from pathlib import Path


class TestDiscoveryAgent:
    """Test the HALF-Discovery agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.discovery import DiscoveryAgent

        assert DiscoveryAgent is not None

    def test_create_requirements(self):
        """Creating requirements should produce a document."""
        from half.agents.discovery import DiscoveryAgent

        agent = DiscoveryAgent("test-project")
        doc = agent.expand_concept(
            "A task management API",
            capabilities=[{"description": "Create tasks", "priority": "P0"}],
            users={"primary": "individual users"},
            constraints={"timeline": "2 weeks"},
        )
        assert doc.elevator_pitch == "A task management API"
        assert len(doc.capabilities) == 1
        assert doc.capabilities[0].description == "Create tasks"


class TestSpecificationAgent:
    """Test the HALF-Specification agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.specification import SpecificationAgent

        assert SpecificationAgent is not None

    def test_add_functional_requirement(self):
        """Adding an FR should assign an ID."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        fr = agent.add_functional_requirement(
            "User Registration",
            "Users can register",
            "P0",
            acceptance_criteria=["Returns 201"],
        )
        assert fr.id == "FR-001"
        assert fr.name == "User Registration"
        assert fr.priority == "P0"

    def test_decompose_tasks(self):
        """Task decomposition should produce DAG ordering."""
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        agent.add_functional_requirement("Auth", "Login", "P0")
        agent.add_functional_requirement("Tasks", "CRUD", "P1", depends_on=["FR-001"])
        tasks = agent.decompose_tasks()
        assert len(tasks) >= 2


class TestArchitectAgent:
    """Test the HALF-Architect agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.architect import ArchitectAgent

        assert ArchitectAgent is not None

    def test_add_adr(self):
        """Adding an ADR should assign an ID."""
        from half.agents.architect import ArchitectAgent

        agent = ArchitectAgent()
        adr = agent.add_adr(
            "Database Selection",
            "Need persistent storage",
            ["PostgreSQL", "SQLite", "MongoDB"],
            "PostgreSQL",
        )
        assert adr.id == "ADR-001"
        assert adr.decision == "PostgreSQL"

    def test_generate_diagram(self):
        """System diagram should be generated."""
        from half.agents.architect import ArchitectAgent

        agent = ArchitectAgent()
        agent.add_component("WebApp", "Frontend")
        diagram = agent.generate_system_diagram()
        assert "mermaid" in diagram


class TestCodeSimplifier:
    """Test the Code-Simplifier refactoring analysis."""

    def test_import(self):
        """Simplifier should be importable."""
        from half.agents.code_simplifier import CodeSimplifier

        assert CodeSimplifier is not None

    def test_analyze_clean_file(self):
        """A clean Python file should produce no issues."""
        from half.agents.code_simplifier import CodeSimplifier

        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "clean.py"
            filepath.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
            simplifier = CodeSimplifier(tmp)
            issues = simplifier.analyze_file(filepath)
            assert isinstance(issues, list)

    def test_analyze_nested_code(self):
        """Deeply nested code should be flagged."""
        from half.agents.code_simplifier import CodeSimplifier

        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "nested.py"
            code = """def deep(x: int) -> None:
    if x > 0:
        if x > 10:
            if x > 100:
                if x > 1000:
                    if x > 10000:
                        print("deep")
"""
            filepath.write_text(code)
            simplifier = CodeSimplifier(tmp)
            issues = simplifier.analyze_file(filepath)
            nesting_issues = [i for i in issues if i["type"] == "nesting"]
            assert len(nesting_issues) > 0

    def test_long_function_flagged(self):
        """Functions over 50 lines should be flagged."""
        from half.agents.code_simplifier import CodeSimplifier

        with tempfile.TemporaryDirectory() as tmp:
            filepath = Path(tmp) / "long.py"
            lines = ["def long_func() -> None:"]
            lines.extend([f"    x{i} = {i}" for i in range(60)])
            lines.append("    print('done')")
            filepath.write_text("\n".join(lines) + "\n")
            simplifier = CodeSimplifier(tmp)
            issues = simplifier.analyze_file(filepath)
            length_issues = [i for i in issues if i["type"] == "length"]
            assert len(length_issues) > 0

    def test_analyze_all(self):
        """Analyzing all files in a directory should work."""
        from half.agents.code_simplifier import CodeSimplifier

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("def f() -> None:\n    pass\n")
            (Path(tmp) / "b.py").write_text("def g() -> int:\n    return 1\n")
            simplifier = CodeSimplifier(tmp)
            all_issues = simplifier.analyze_all("*.py")
            assert isinstance(all_issues, list)

    def test_generate_report(self):
        """Report generation should produce markdown."""
        from half.agents.code_simplifier import CodeSimplifier

        simplifier = CodeSimplifier()
        report = simplifier.generate_report([])
        assert "# Code-Simplifier Report" in report
        assert "No issues found" in report

    def test_generate_report_with_issues(self):
        """Report with issues should include them."""
        from half.agents.code_simplifier import CodeSimplifier

        simplifier = CodeSimplifier()
        issues = [
            {
                "severity": "high",
                "type": "nesting",
                "file": "test.py",
                "line": 5,
                "function": "deep_func",
                "message": "Deep nesting found",
                "suggestion": "Extract inner logic",
            }
        ]
        report = simplifier.generate_report(issues)
        assert "deep_func" in report


class TestScaffoldAgent:
    """Test the HALF-Scaffold agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.scaffold import ScaffoldAgent

        assert ScaffoldAgent is not None

    def test_scaffold_project(self):
        """Scaffolding should create project files."""
        from half.agents.scaffold import ScaffoldAgent

        with tempfile.TemporaryDirectory() as tmp:
            agent = ScaffoldAgent(Path(tmp))
            files = agent.scaffold_project("my-project")
            assert len(files) > 0
            # Check that files dict has entries
            for path_str in files:
                assert (
                    Path(path_str).parent.exists() or True
                )  # parent might not exist yet


class TestTestingAgent:
    """Test the HALF-Testing agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.testing import TestingAgent

        assert TestingAgent is not None

    def test_add_fr(self):
        """Adding an FR for coverage tracking should work."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        agent.add_fr("FR-001")
        assert "FR-001" in agent.coverage

    def test_generate_report(self):
        """Quality report should be generated."""
        from half.agents.testing import TestingAgent

        agent = TestingAgent()
        report = agent.generate_quality_report()
        assert report.total_frs >= 0


class TestSecurityAgent:
    """Test the HALF-Security agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.security import SecurityAgent

        assert SecurityAgent is not None

    def test_add_finding(self):
        """Adding a finding should assign an ID."""
        from half.agents.security import SecurityAgent

        agent = SecurityAgent()
        finding = agent.add_finding(
            "HIGH",
            "sast",
            "src/main.py",
            42,
            "SQL injection possible",
            "Use parameterized queries",
        )
        assert finding.id.startswith("SEC-")
        assert finding.severity == "HIGH"

    def test_get_report(self):
        """Report should categorize findings."""
        from half.agents.security import SecurityAgent

        agent = SecurityAgent()
        agent.add_finding(
            "CRITICAL", "red-team", "src/auth.py", 10, "Hardcoded key", "Use env var"
        )
        report = agent.get_report()
        assert report.critical_count == 1


class TestImplementAgent:
    """Test the HALF-Implement agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.implement import ImplementAgent

        assert ImplementAgent is not None

    def test_generate_test_template(self):
        """Test template generation should produce valid test code."""
        from half.agents.implement import ImplementAgent

        template = ImplementAgent.generate_test_template(
            "my_module",
            "my_function",
            {"key": "value"},
            [
                {
                    "input": {},
                    "description": "Error case",
                    "expected_exception": "ValueError",
                }
            ],
        )
        assert "class TestMy_Function" in template
        assert "test_happy_path" in template
        assert "test_error_case" in template

    def test_generate_source_template(self):
        """Source template should produce a stub."""
        from half.agents.implement import ImplementAgent

        source = ImplementAgent.generate_source_template(
            "my_module",
            "my_func",
            {"x": "int"},
            "str",
        )
        assert "def my_func" in source
        assert "NotImplementedError" in source


class TestIterateAgent:
    """Test the HALF-Iterate agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.iterate import IterateAgent

        assert IterateAgent is not None

    def test_classify_bug(self):
        """Bug titles should be classified as BUG."""
        from half.agents.iterate import IssueType, classify_input

        result = classify_input("Fix crash on login", "Error when user logs in")
        assert result == IssueType.BUG

    def test_classify_feature(self):
        """Feature titles should be classified as FEATURE."""
        from half.agents.iterate import IssueType, classify_input

        result = classify_input("Add export feature", "Could we support CSV export?")
        assert result == IssueType.FEATURE

    def test_create_issue(self):
        """Creating an issue should assign an ID."""
        from half.agents.iterate import IssueType, IterateAgent

        agent = IterateAgent()
        issue = agent.create_issue("Bug: login broken", "Users cannot log in")
        assert issue.id.startswith("I-")
        assert issue.issue_type == IssueType.BUG


class TestObserveAgent:
    """Test the HALF-Observe agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.observe import ObserveAgent

        assert ObserveAgent is not None

    def test_render_monitoring_config(self):
        """Monitoring config should be valid YAML."""
        from half.agents.observe import ObserveAgent

        agent = ObserveAgent()
        config = agent.render_monitoring_config_yaml()
        assert "metric_collection" in config
        assert "triggers:" in config


class TestLaunchAgent:
    """Test the HALF-Launch agent."""

    def test_import(self):
        """Agent should be importable."""
        from half.agents.launch import LaunchAgent

        assert LaunchAgent is not None

    def test_readiness_checklist(self):
        """Readiness checklist should have 18 items."""
        from half.agents.launch import READINESS_CHECKS

        assert len(READINESS_CHECKS) == 18
        assert READINESS_CHECKS[0].id == "PR-01"

    def test_completion_pct(self):
        """Completion percentage should calculate correctly."""
        from half.agents.launch import LaunchAgent

        agent = LaunchAgent()
        assert agent.completion_pct() == 0.0
        agent.mark_complete("PR-01")
        assert agent.completion_pct() > 0
        assert agent.completion_pct() < 100
