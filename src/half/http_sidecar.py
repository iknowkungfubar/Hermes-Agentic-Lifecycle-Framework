"""HALF — Sidecar HTTP Server for GUI.

Simple HTTP server that the Tauri GUI frontend queries for pipeline data.
Runs as a background process alongside the GUI.
"""

from __future__ import annotations

import json
import logging
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

from half.half_sidecar import cmd_generate_mrp, cmd_status

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("half.http_sidecar")


class HalfAPIHandler(BaseHTTPRequestHandler):
    """Serves HALF pipeline data as JSON over HTTP."""

    def do_GET(self) -> None:
        if self.path in {"/api/status", "/api/get_pipeline_status"}:
            data = cmd_status()
            self._json_response(data)
        elif self.path == "/api/get_finality_gate_status":
            import os

            gate_file = ".hale/finality-gate.json"
            if os.path.exists(gate_file):
                with open(gate_file) as f:
                    data = json.load(f)
            else:
                data = {
                    "locked": True,
                    "mrp_ready": False,
                    "deployment_approved": False,
                }
            self._json_response(data)
        elif self.path in {"/api/generate-mrp", "/api/generate_mrp"}:
            data = cmd_generate_mrp()
            self._json_response(data)
        elif self.path == "/api/approve_deployment":
            self._json_response(
                {"status": "error", "message": "Use POST with signature body"}
            )
        elif self.path == "/api/vram":
            self._json_response(self._get_vram())
        elif self.path == "/api/stalled":
            self._json_response({"stalled": self._get_stalled()})
        elif self.path == "/api/diff":
            self._json_response(self._get_diff())
        elif self.path == "/api/health":
            from half import __version__
            import os
            self._json_response({"status": "ok", "version": __version__, "host": os.uname().nodename})
        else:
            self._json_response(
                {"status": "error", "message": f"Unknown endpoint: {self.path}"}, 404
            )

    def do_POST(self) -> None:
        if self.path == "/api/approve_deployment":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            signature = data.get("signature", "")
            if len(signature) >= 8:
                import os

                gate_data = {
                    "status": "approved",
                    "signature": signature,
                    "locked": False,
                    "mrp_ready": True,
                    "deployment_approved": True,
                }
                os.makedirs(".hale", exist_ok=True)
                with open(".hale/finality-gate.json", "w") as f:
                    json.dump(gate_data, f)
                self._json_response({"status": "ok", "message": "Deployment approved"})
            else:
                self._json_response(
                    {"status": "error", "message": "Signature too short"}, 400
                )
        else:
            self._json_response(
                {"status": "error", "message": f"Unknown endpoint: {self.path}"}, 404
            )

    def _json_response(self, data: dict[str, object], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _get_vram(self) -> dict[str, object]:
        try:
            from half.vram_monitor import VRAMMonitor

            return VRAMMonitor().to_dict()
        except Exception as e:
            return {"error": str(e)[:100]}

    def _get_stalled(self) -> list[dict[str, object]]:
        try:
            from half.stale_monitor import StaleSessionMonitor

            monitor = StaleSessionMonitor()
            sessions = monitor.scan()
            return [
                {
                    "type": s.type,
                    "name": s.name,
                    "age_hours": round(s.age_hours, 1),
                    "action": s.action,
                }
                for s in sessions
            ]
        except Exception:
            return []

    def _get_diff(self) -> dict[str, object]:
        try:
            diff_result = subprocess.run(
                ["git", "diff", "HEAD~1", "--stat"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {"diff": diff_result.stdout[:2000]}
        except Exception:
            return {"diff": ""}

    def log_message(self, format: str, *args: str) -> None:
        logger.info("%s - %s", self.client_address[0], format % args)


def run_server(host: str = "127.0.0.1", port: int = 9721) -> None:
    """Start the HTTP sidecar server."""
    server = HTTPServer((host, port), HalfAPIHandler)
    logger.info("HALF sidecar HTTP server at http://%s:%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    run_server()
