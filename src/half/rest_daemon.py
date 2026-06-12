"""HALF — REST API Daemon: Headless Commander Agent.

Serves the HALF pipeline as a REST API, allowing integration with
external CI pipelines or chat platforms.

Usage:
    python -m half.rest_daemon [--port 31337] [--host 127.0.0.1]

Based on the HALF doctrine's 'goal serve --port 31337' specification.
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from half.doctor import run_doctor
from half.half_sidecar import (
    cmd_gate_check,
    cmd_generate_mrp,
    cmd_run_phase,
    cmd_status,
)

logger = logging.getLogger("half.rest_daemon")


class RESTAPIHandler(BaseHTTPRequestHandler):
    """REST API for the HALF Commander Agent."""

    def do_GET(self) -> None:
        if self.path in {"/health", "/"}:
            self._json({"status": "ok", "service": "HALF REST Daemon"})
        elif self.path == "/status":
            self._json(cmd_status())
        elif self.path == "/doctor":
            report = run_doctor()
            self._json(report.to_dict())
        elif self.path == "/mrp":
            self._json(cmd_generate_mrp())
        elif self.path == "/ralph":
            from half.ralph_loop import RalphLoop

            ralph = RalphLoop()
            ralph_report = ralph.run()
            self._json(
                {
                    "status": "ok",
                    "findings": len(ralph_report.findings),
                    "branches": ralph_report.branch_count,
                }
            )
        elif self.path == "/digest":
            from half.pda_digest import PDADigest

            digest = PDADigest()
            briefing = digest.generate_briefing()
            self._json({"status": "ok", "briefing": briefing})
        else:
            self._json({"error": f"Unknown endpoint: {self.path}"}, 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if self.path == "/run-phase":
            phase = data.get("phase", "")
            result = cmd_run_phase(phase) if phase else {"error": "phase required"}
            self._json(result)
        elif self.path == "/gate-check":
            phase = data.get("phase", "")
            result = cmd_gate_check(phase) if phase else {"error": "phase required"}
            self._json(result)
        elif self.path == "/approve":
            sig = data.get("signature", "")
            self._json({"status": "approved" if len(sig) >= 8 else "error"})
        elif self.path == "/digest/speak":
            from half.pda_digest import PDADigest

            digest = PDADigest()
            briefing = digest.generate_briefing()
            digest.speak_briefing(briefing)
            self._json({"status": "ok", "message": "Briefing spoken"})
        else:
            self._json({"error": f"Unknown endpoint: {self.path}"}, 404)

    def _json(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_OPTIONS(self) -> None:
        self._json({})

    def log_message(self, fmt: str, *args: str) -> None:
        logger.info("%s - %s", self.client_address[0], fmt % args)


def run_server(host: str = "127.0.0.1", port: int = 31337) -> None:
    """Start the HALF REST API daemon.

    Args:
        host: Bind address (default: 127.0.0.1 for security).
        port: Port to listen on (default: 31337).
    """
    server = HTTPServer((host, port), RESTAPIHandler)
    logger.info("HALF REST Daemon listening on http://%s:%d", host, port)
    logger.info(
        "Endpoints: /health, /status, /doctor, /mrp, /ralph, /digest, /run-phase, /gate-check"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HALF REST API Daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=31337, help="Port")
    args = parser.parse_args()
    run_server(args.host, args.port)
