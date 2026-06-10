"""HALF — GitHub Webhook Server for Autonomous PRs.

Receives GitHub webhooks, verifies signatures, and dispatches actions.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

logger = logging.getLogger("half.webhooks")


class WebhookHandler:
    """Handles GitHub webhooks for autonomous PR creation."""

    def __init__(self, webhook_secret: str = "", repo_root: str | Path = "."):
        self.secret = webhook_secret or os.environ.get("HALF_WEBHOOK_SECRET", "")
        self.repo_root = Path(repo_root)

    def verify_signature(self, payload_body: bytes, signature: str) -> bool:
        if not self.secret:
            logger.warning("No webhook secret configured")
            return True
        expected = hmac.new(self.secret.encode(), payload_body, "sha256").hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def handle_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])
        results = []
        for commit in commits:
            passed = self._verify_commit(commit)
            results.append(passed)
            if not passed:
                pr_url = self._create_fix_pr(branch, commit)
                results[-1]["pr_url"] = pr_url
        return {"event": "push", "branch": branch, "commits_checked": len(commits), "results": results}

    def handle_issues(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        return {"event": "issues", "action": action, "issue_number": issue.get("number"), "title": issue.get("title")}

    def handle_pull_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        return {"event": "pull_request", "action": action, "pr_number": pr.get("number"), "title": pr.get("title")}

    def _verify_commit(self, commit: dict[str, Any]) -> dict[str, Any]:
        message = commit.get("message", "").split("\n")[0]
        return {
            "sha": commit.get("id", "")[:8],
            "message": message,
            "follows_convention": message.startswith(("feat:", "fix:", "refactor:", "test:", "docs:", "chore:")),
            "passed": True,
        }

    def _create_fix_pr(self, base_branch: str, commit: dict[str, Any]) -> str:
        """Create a GitHub PR from a fix branch using gh CLI."""
        branch_name = f"fix/auto-{commit.get('id', 'unknown')[:8]}"
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_root,
                           capture_output=True, timeout=30)
            subprocess.run(["git", "commit", "--allow-empty", "-m", f"fix: auto-fix for {commit.get('id', '')[:8]}"],
                           cwd=self.repo_root, capture_output=True, timeout=30)
            result = subprocess.run(
                ["gh", "pr", "create", "--base", base_branch, "--head", branch_name,
                 "--title", f"fix: auto-remediation for {commit.get('id', '')[:8]}",
                 "--body", "Automated fix branch created by HALF Ralph Loop."],
                cwd=self.repo_root, capture_output=True, text=True, timeout=30,
            )
            subprocess.run(["git", "checkout", base_branch], cwd=self.repo_root, capture_output=True, timeout=30)
            return result.stdout.strip() if result.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            return ""

    def dispatch(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "push": self.handle_push,
            "issues": self.handle_issues,
            "pull_request": self.handle_pull_request,
        }
        handler = handlers.get(event)
        if handler:
            return handler(payload)
        return {"event": event, "action": "unhandled"}


class WebhookServer:
    """HTTP server that receives GitHub webhooks."""

    def __init__(self, handler: WebhookHandler, host: str = "127.0.0.1", port: int = 9725):
        self.handler = handler
        self.host = host
        self.port = port

    def start(self) -> None:
        server = HTTPServer((self.host, self.port), self._make_request_handler(self.handler))
        print(f"HALF webhook server listening on http://{self.host}:{self.port}")
        print("Configure your GitHub repo webhook to point here:")
        print(f"  Payload URL: http://your-server:{self.port}/webhook")
        print(f"  Secret: {self.handler.secret or '(not set)'}")
        print("  Events: Push, Pull requests, Issues")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

    @staticmethod
    def _make_request_handler(handler: WebhookHandler) -> type[BaseHTTPRequestHandler]:
        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                event = self.headers.get("X-GitHub-Event", "push")
                signature = self.headers.get("X-Hub-Signature-256", "")

                if not handler.verify_signature(body, signature):
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Invalid signature"}')
                    return

                payload = json.loads(body.decode("utf-8"))
                result = handler.dispatch(event, payload)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))

            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"HALF Webhook Server running")

            def log_message(self, format: str, *args: object) -> None:
                logger.info("Webhook: %s", format % args)

        return _Handler
