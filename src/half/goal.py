"""HALF — Goal CLI Sidecar.

The 'goal' CLI is the primary sidecar for the Tauri Command Center.
It provides the same functionality as 'half' but with JSON-only output
suitable for programmatic consumption.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Goal CLI — JSON-only interface for the Tauri sidecar."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        sys.exit(1)

    command = sys.argv[1]
    result: dict[str, object] = {"error": f"Unknown command: {command}"}

    try:
        if command == "status":
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
        elif command == "continue" and len(sys.argv) > 2:
            result = {"status": "resumed", "checkpoint_id": sys.argv[2]}
    except Exception as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
