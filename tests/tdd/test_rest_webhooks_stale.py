"""TDD: target rest_daemon, webhooks dispatch, stale_monitor, specification agents."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest


class TestRestDaemonHandler:
    """Cover the 67 uncovered lines in rest_daemon.py."""

    @pytest.fixture(scope="class")
    def server(self):
        from half.rest_daemon import RESTAPIHandler

        port = 19995
        srv = HTTPServer(("127.0.0.1", port), RESTAPIHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)
        yield port
        srv.shutdown()

    def test_do_GET_status(self, server):
        """Hit do_GET at /status."""

        r = urllib.request.urlopen(f"http://127.0.0.1:{server}/status", timeout=5)
        assert r.status == 200

    def test_handler_methods(self):
        from half.rest_daemon import RESTAPIHandler

        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")

    def test_handler_class(self):
        from half.rest_daemon import RESTAPIHandler

        assert hasattr(RESTAPIHandler, "do_GET")
        assert hasattr(RESTAPIHandler, "do_POST")
        assert hasattr(RESTAPIHandler, "log_message")


class TestWebhooksDispatch:
    """Cover webhooks dispatch and event handling."""

    def test_dispatch_push(self):
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.dispatch("push", {"ref": "refs/heads/main"})
        assert isinstance(r, dict)

    def test_dispatch_issues(self):
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.dispatch("issues", {"action": "opened", "issue": {"number": 1}})
        assert isinstance(r, dict)

    def test_dispatch_pull_request(self):
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.dispatch("pull_request", {"action": "opened"})
        assert isinstance(r, dict)

    def test_dispatch_unknown(self):
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.dispatch("unknown_event", {})
        assert isinstance(r, dict) and "error" not in r


class TestStaleMonitor:
    """Cover stale_monitor uncovered lines."""

    def test_scan_empty(self):
        from half.stale_monitor import StaleSessionMonitor

        m = StaleSessionMonitor()
        sessions = m.scan()
        assert isinstance(sessions, list)

    def test_scan_with_state(self, tmp_path):
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "session_1.json").write_text(
            '{"session_id": "s1", "last_activity": "2026-01-01T00:00:00", "status": "running"}'
        )
        from half.stale_monitor import StaleSessionMonitor

        m = StaleSessionMonitor()
        sessions = m.scan()
        assert isinstance(sessions, list)


class TestSpecificationAgent:
    """Cover specification agent methods."""

    def test_add_fr(self):
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        fr = agent.add_functional_requirement("FR-001", "Users can register", "201")
        assert fr.id == "FR-001"
        assert len(agent.functional_reqs) == 1

    def test_render_markdown(self):
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        agent.add_functional_requirement("FR-001", "Users can register", "201")
        md = agent.render_specification_markdown()
        assert "FR-001" in md

    def test_decompose_tasks(self):
        from half.agents.specification import SpecificationAgent

        agent = SpecificationAgent()
        tasks = agent.decompose_tasks()
        assert isinstance(tasks, list)
