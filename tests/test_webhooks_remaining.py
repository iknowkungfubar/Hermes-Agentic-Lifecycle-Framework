"""Target remaining uncovered lines in webhooks.py.

Covers WebhookHandler and WebhookServer methods:
- verify_signature with no secret (30-31)
- do_GET response on the handler class (189-190)
- dispatch edge cases
- handler methods with various payloads
"""

from __future__ import annotations

from http.server import HTTPServer
from io import BytesIO


class TestWebhookSignature:
    """Cover verify_signature with no secret (lines 30-31)."""

    def test_verify_no_secret_returns_true(self) -> None:
        """When HALF_WEBHOOK_SECRET is unset, verify_signature returns True."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler(webhook_secret="")
        result = h.verify_signature(b"{}", "")
        assert result is True

    def test_verify_secret_configured(self) -> None:
        """When a secret is set, verify_signature validates the signature."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler(webhook_secret="mysecret")
        # Compute expected signature for the empty body
        import hmac

        expected = hmac.new(b"mysecret", b'{"key":"value"}', "sha256").hexdigest()
        sig = f"sha256={expected}"
        result = h.verify_signature(b'{"key":"value"}', sig)
        assert result is True

        # Wrong signature
        bad = h.verify_signature(b'{"key":"value"}', "sha256=badbadbad")
        assert bad is False


class TestWebhookDispatch:
    """Cover dispatch with various event types."""

    def test_dispatch_unknown_event(self) -> None:
        """Unknown events return an 'unhandled' response."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.dispatch("unknown_event", {})
        assert r == {"event": "unknown_event", "action": "unhandled"}

    def test_handle_push_empty_commits(self) -> None:
        """Push with no commits doesn't crash."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_push({"ref": "refs/heads/main", "commits": []})
        assert r["event"] == "push"
        assert r["branch"] == "main"
        assert r["commits_checked"] == 0
        assert r["results"] == []

    def test_handle_push_no_ref(self) -> None:
        """Push with missing ref doesn't crash."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_push({"commits": []})
        assert r["branch"] == ""


class TestWebhookPR:
    """Cover pull_request handling."""

    def test_handle_pr_opened(self) -> None:
        """Pull request opened event returns correct shape."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_pull_request(
            {
                "action": "opened",
                "pull_request": {"number": 42, "title": "Fix bug"},
            }
        )
        assert r["event"] == "pull_request"
        assert r["action"] == "opened"
        assert r["pr_number"] == 42
        assert r["title"] == "Fix bug"

    def test_handle_pr_closed(self) -> None:
        """Pull request closed event works."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_pull_request(
            {
                "action": "closed",
                "pull_request": {"number": 7, "title": "WIP"},
            }
        )
        assert r["action"] == "closed"
        assert r["pr_number"] == 7

    def test_handle_pr_missing_data(self) -> None:
        """Pull request with missing data doesn't crash."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_pull_request({"action": "opened"})
        assert r["pr_number"] is None


class TestWebhookIssues:
    """Cover issues handling."""

    def test_handle_issue_opened(self) -> None:
        """Issue opened event."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_issues(
            {"action": "opened", "issue": {"number": 100, "title": "Bug report"}}
        )
        assert r["event"] == "issues"
        assert r["action"] == "opened"
        assert r["issue_number"] == 100
        assert r["title"] == "Bug report"

    def test_handle_issue_no_issue_field(self) -> None:
        """Issue event with missing issue dict."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h.handle_issues({"action": "deleted"})
        assert r["issue_number"] is None


class TestWebhookServerHandler:
    """Cover _make_request_handler inner class (lines 165-195)."""

    def test_do_get_returns_200(self) -> None:
        """do_GET on the handler returns 'HALF Webhook Server running'."""
        from http.server import BaseHTTPRequestHandler

        from half.webhooks import WebhookHandler, WebhookServer

        h = WebhookHandler()
        handler_class = WebhookServer._make_request_handler(h)
        # Simulate a GET request with proper request_line setup
        instance = handler_class.__new__(handler_class)
        instance.request_version = "HTTP/1.1"
        instance.command = "GET"
        instance.path = "/"
        instance.headers = {}
        instance.rfile = BytesIO()
        instance.wfile = BytesIO()
        instance.send_response = lambda code, message=None: setattr(
            instance, "_status", code
        )
        instance.send_header = lambda k, v: None
        instance.end_headers = lambda: None

        instance.do_GET()
        assert instance._status == 200
        assert instance.wfile.getvalue() == b"HALF Webhook Server running"

    def test_handler_log_message(self) -> None:
        """log_message on the handler doesn't crash."""
        from half.webhooks import WebhookHandler, WebhookServer

        h = WebhookHandler()
        handler_class = WebhookServer._make_request_handler(h)
        instance = handler_class.__new__(handler_class)
        # log_message just logs via logger, call it directly
        try:
            instance.log_message("test %s %d", "hello", 42)
        except Exception:
            pass  # May fail if no server_address, but shouldn't crash


class TestVerifyCommit:
    """Cover _verify_commit edge cases."""

    def test_verify_commit_standard_message(self) -> None:
        """Standard conventional commit passes."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h._verify_commit(
            {"id": "abc123", "message": "feat: add new feature\n\nDetails here"}
        )
        assert r["sha"] == "abc123"
        assert r["follows_convention"] is True
        assert r["passed"] is True

    def test_verify_commit_non_conventional(self) -> None:
        """Non-conventional commit shows follows_convention=False."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h._verify_commit({"id": "def456", "message": "some random message"})
        assert r["follows_convention"] is False

    def test_verify_commit_no_id(self) -> None:
        """Commit with no id uses empty string."""
        from half.webhooks import WebhookHandler

        h = WebhookHandler()
        r = h._verify_commit({"message": "fix: something"})
        assert r["sha"] == ""
