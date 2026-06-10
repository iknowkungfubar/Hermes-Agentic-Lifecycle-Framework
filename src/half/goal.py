"""HALF — Goal CLI Sidecar.

Primary JSON-only CLI for the Tauri Command Center.
Supports all HALF commands with structured output.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    """Goal CLI entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified", "commands": [
            "status", "run-phase <phase>", "gate-check <phase>",
            "generate-mrp", "continue <checkpoint_id>",
            "voice stt <file>", "voice tts <text>",
            "focalboard create", "serve", "version",
        ]}))
        sys.exit(1)

    command = sys.argv[1]
    result: dict[str, object] = {"error": f"Unknown command: {command}"}

    try:
        if command == "version":
            from half import __version__
            result = {"version": __version__, "name": "HALF Goal CLI"}
        elif command == "status":
            from half.half_sidecar import cmd_status
            result = cmd_status()
        elif command == "run-phase" and len(sys.argv) > 2:
            from half.half_sidecar import cmd_run_phase
            result = cmd_run_phase(sys.argv[2])
        elif command == "gate-check" and len(sys.argv) > 2:
            from half.half_sidecar import cmd_gate_check
            result = cmd_gate_check(sys.argv[2])
        elif command == "generate-mrp":
            from half.half_sidecar import cmd_generate_mrp
            result = cmd_generate_mrp()
        elif command == "continue":
            result = {"status": "resumed", "checkpoint_id": sys.argv[2] if len(sys.argv) > 2 else "latest"}
        elif command == "voice" and len(sys.argv) > 3:
            if sys.argv[2] == "stt":
                from half.half_sidecar import cmd_voice_stt
                result = cmd_voice_stt(sys.argv[3])
            elif sys.argv[2] == "tts":
                from half.half_sidecar import cmd_voice_tts
                result = cmd_voice_tts(" ".join(sys.argv[3:]))
        elif command == "focalboard" and len(sys.argv) > 2 and sys.argv[2] == "create":
            from half.half_sidecar import cmd_focalboard_create
            result = cmd_focalboard_create()
        elif command == "serve":
            from half.half_sidecar import _run_http_server
            _run_http_server()
            return
    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
