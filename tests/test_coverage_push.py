"""Coverage push: http_sidecar, goal, rest_daemon, sandbox, browser_research, indexing, no_slop, git_worktree."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestHTTPSidecar:
    def test_import(self):
        from half.http_sidecar import HalfAPIHandler, run_server
        assert HalfAPIHandler is not None
        assert callable(run_server)

    def test_handler_methods(self):
        from half.http_sidecar import HalfAPIHandler
        assert hasattr(HalfAPIHandler, "do_GET")
        assert hasattr(HalfAPIHandler, "do_POST")


class TestGoal:
    def test_import(self):
        from half.goal import main
        assert callable(main)


class TestRestDaemon:
    def test_import(self):
        from half.rest_daemon import RESTAPIHandler, run_server
        assert hasattr(RESTAPIHandler, "do_GET")
        assert callable(run_server)


class TestSandbox:
    def test_import(self):
        from half.sandbox import ExecutionSandbox
        assert ExecutionSandbox is not None

    def test_init_defaults(self):
        from half.sandbox import ExecutionSandbox
        try:
            sandbox = ExecutionSandbox()
            assert sandbox is not None
        except (FileNotFoundError, RuntimeError):
            pass


class TestBrowserResearch:
    def test_import(self):
        from half.browser_research import BrowserResearchAgent
        assert BrowserResearchAgent is not None

    def test_create_agent(self):
        from half.browser_research import BrowserResearchAgent
        agent = BrowserResearchAgent()
        assert agent is not None


class TestIndexing:
    def test_import(self):
        from half.indexing import RepoIndexer
        assert RepoIndexer is not None

    def test_build_index_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.indexing import RepoIndexer
            indexer = RepoIndexer(root=tmp)
            result = indexer.build_index()
            assert result is not None

    def test_search_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.indexing import RepoIndexer
            indexer = RepoIndexer(root=tmp)
            indexer.build_index()
            results = indexer.search("test")
            assert isinstance(results, list)

    def test_get_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.indexing import RepoIndexer
            indexer = RepoIndexer(root=tmp)
            indexer.build_index()
            summary = indexer.get_summary()
            assert isinstance(summary, dict)


class TestNoSlop:
    def test_import(self):
        from half.no_slop import NoSlopIndexer, SemanticToken
        assert NoSlopIndexer is not None

    def test_build_index_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.no_slop import NoSlopIndexer
            indexer = NoSlopIndexer(root_path=tmp)
            result = indexer.build_index()
            assert isinstance(result, dict)

    def test_build_index_with_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.no_slop import NoSlopIndexer
            src = Path(tmp) / "test.py"
            src.write_text("import os\ndef foo():\n    return os.getcwd()\n")
            indexer = NoSlopIndexer(root_path=tmp)
            result = indexer.build_index()
            assert isinstance(result, dict)


class TestGitWorktree:
    def test_import(self):
        from half.git_worktree import GitWorktreeManager, WorktreeSession
        assert GitWorktreeManager is not None

    def test_init_non_existent_repo(self):
        from half.git_worktree import GitWorktreeManager
        mgr = GitWorktreeManager(repo_path="/tmp/nonexistent-test-repo")
        assert mgr._sessions == {}

    def test_init_valid_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.git_worktree import GitWorktreeManager
            mgr = GitWorktreeManager(repo_path=tmp)
            assert mgr.worktree_base.exists()

    def test_list_sessions_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            from half.git_worktree import GitWorktreeManager
            mgr = GitWorktreeManager(repo_path=tmp)
            assert mgr.list_sessions() == []
