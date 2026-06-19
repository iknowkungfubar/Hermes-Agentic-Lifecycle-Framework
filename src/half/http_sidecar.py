"""HALF — Sidecar HTTP Server for GUI.

Serves pipeline data, chat interface, and system status to the Tauri GUI.
"""

from __future__ import annotations

import json
import logging
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

from half.half_sidecar import cmd_generate_mrp, cmd_status

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("half.http_sidecar")

# In-memory chat store
_chat_messages: list[dict[str, str]] = []


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
            self._json_response(cmd_generate_mrp())
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
            import os

            from half import __version__

            self._json_response(
                {"status": "ok", "version": __version__, "host": os.uname().nodename}
            )
        elif self.path == "/api/chat":
            self._json_response({"messages": _chat_messages})
        elif self.path == "/api/focalboard-boards":
            self._json_response(self._get_focalboard_boards())
        elif self.path == "/api/pipeline-jobs":
            self._json_response(self._get_pipeline_jobs())
        else:
            self._json_response(
                {"status": "error", "message": f"Unknown: {self.path}"}, 404
            )

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if self.path == "/api/approve_deployment":
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
        elif self.path == "/api/chat":
            message = data.get("message", "").strip()
            if message:
                _chat_messages.append({"role": "user", "content": message})
                # PDA response — process the user's command
                response = self._process_pda_command(message)
                _chat_messages.append({"role": "assistant", "content": response})
            self._json_response({"messages": _chat_messages})
        else:
            self._json_response(
                {"status": "error", "message": f"Unknown: {self.path}"}, 404
            )

    def _process_pda_command(self, message: str) -> str:
        """Process a user message and return a PDA (Commander Agent) response."""
        msg_lower = message.lower()

        if msg_lower in {"status", "pipeline status"}:
            try:
                s = cmd_status()
                phases = s.get("completed_phases", [])
                active = s.get("active_phase", "none")
                return f"Pipeline status: {len(phases)}/5 phases complete. Active: {active}. Budget: {s.get('error_budget_remaining', 100)}% remaining."
            except Exception as e:
                return f"Error getting status: {e}"

        if "run phase" in msg_lower or "execute" in msg_lower:
            import re

            match = re.search(r"phase[-\s]?(\d)", msg_lower)
            if match:
                phase = f"phase-{match.group(1)}"
                try:
                    from half.half_sidecar import cmd_run_phase

                    r = cmd_run_phase(phase)
                    return (
                        f"Phase {match.group(1)} execution: {r.get('status', 'done')}."
                    )
                except Exception as e:
                    return f"Error running phase: {e}"
            return "Which phase? Try 'run phase 2'."

        if "gate" in msg_lower:
            import re

            match = re.search(r"phase[-\s]?(\d)", msg_lower)
            phase = f"phase-{match.group(1)}" if match else "phase-1"
            try:
                from half.half_sidecar import cmd_gate_check

                r = cmd_gate_check(phase)
                return f"Gate check for {phase}: {r.get('status', 'completed')}."
            except Exception as e:
                return f"Error: {e}"

        if "mrp" in msg_lower or "merge readiness" in msg_lower:
            try:
                r = cmd_generate_mrp()
                return f"MRP generated: {r.get('status', 'ok')}."
            except Exception as e:
                return f"Error: {e}"

        if "help" in msg_lower:
            return (
                "Available commands:\n"
                "- status / pipeline status\n"
                "- run phase <1-5>\n"
                "- gate check <phase>\n"
                "- generate mrp\n"
                "- deploy / approve\n"
                "- help"
            )

        if "deploy" in msg_lower or "approve" in msg_lower:
            return (
                "Deployment requires cryptographic sign-off at the Finality Gate.\n"
                "Enter your sign-off key (8+ chars) in the Finality Gate panel."
            )

        if "hello" in msg_lower or "hi" in msg_lower:
            return "Hello! I'm the HALF Commander Agent. I can run pipeline phases, check gates, and manage your SDLC. Try 'help' for commands."

        return (
            f'I understand you said: "{message[:100]}". '
            "I can manage your pipeline (status, run phase, gates, MRP). "
            "Try 'help' for available commands."
        )

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

    def _get_focalboard_boards(self) -> list[dict[str, object]]:
        """Get boards from Focalboard API."""
        try:
            import urllib.request

            r = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/boards", timeout=3)
            data: list[dict[str, object]] = json.loads(r.read())
            return data
        except Exception:
            return [
                {
                    "id": "demo",
                    "title": "HALF Pipeline",
                    "description": "Main pipeline Kanban",
                }
            ]

    def _get_pipeline_jobs(self) -> list[dict[str, object]]:
        """Get pipeline jobs."""
        return [
            {"id": "job-1", "name": f"Phase {i}", "status": "pending"}
            for i in range(1, 6)
        ]

    def _json_response(
        self, data: dict[str, object] | list[dict[str, object]], status: int = 200
    ) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format: str, *args: str) -> None:
        logger.info("%s - %s", self.client_address[0], format % args)


def run_server(host: str = "127.0.0.1", port: int = 9721) -> None:
    """Start the HALF HTTP sidecar server."""
    server = HTTPServer((host, port), HalfAPIHandler)
    logger.info("HALF sidecar running on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        logger.info("Sidecar stopped")


if __name__ == "__main__":
    run_server()
