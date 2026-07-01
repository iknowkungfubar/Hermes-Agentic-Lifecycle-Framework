#!/usr/bin/env python3
"""HALF — Command-Line Interface.

Usage:
    half --help
    half init [--project NAME] [--mode MODE] [--dir PATH]
    half status
    half run-phase <phase>
    half gate-check <phase>
    half generate-mrp
    half voice stt <file>
    half voice tts <text>
    half focalboard create
    half version
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Main CLI entrypoint for HALF."""
    parser = argparse.ArgumentParser(
        prog="half",
        description="Hermes Agentic Lifecycle Framework — Autonomous SDLC orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="store_true", help="Show HALF version and exit"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init — actually calls genesis.sh
    init_p = subparsers.add_parser("init", help="Initialize a new HALF project")
    init_p.add_argument("--project", default="my-app", help="Project name")
    init_p.add_argument(
        "--mode",
        default="full",
        choices=["full", "prototype", "patch", "audit"],
        help="Pipeline mode",
    )
    init_p.add_argument(
        "--dir", default="", help="Target directory (defaults to project name)"
    )

    subparsers.add_parser("status", help="Show pipeline status")
    rp = subparsers.add_parser("run-phase", help="Execute a pipeline phase")
    rp.add_argument("phase", help="Phase identifier (e.g., phase-1)")
    rp.add_argument(
        "--concept",
        default="",
        help="Project concept/idea for the Discovery agent to analyze",
    )
    gp = subparsers.add_parser("gate-check", help="Run gate checks for a phase")
    gp.add_argument("phase", help="Phase identifier (e.g., phase-1)")
    subparsers.add_parser("generate-mrp", help="Generate Merge-Readiness Pack")

    vp = subparsers.add_parser("voice", help="Voice commands (STT/TTS)")
    vs = vp.add_subparsers(dest="voice_cmd")
    vs.add_parser("stt").add_argument("file", help="Path to audio file")
    vs.add_parser("tts").add_argument("text", help="Text to speak")

    fbp = subparsers.add_parser("focalboard", help="Focalboard Kanban integration")
    fbs = fbp.add_subparsers(dest="fb_cmd")
    fbs.add_parser("create", help="Create a Focalboard board")

    subparsers.add_parser("version", help="Show HALF version")

    args = parser.parse_args()

    if args.version:
        _show_version()
        return

    if not args.command:
        parser.print_help()
        return

    try:
        result = _route_command(args)
        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        elif result is not None:
            print(result)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _show_version() -> None:
    """Print HALF version."""
    from half import __description__, __license__, __version__

    print(f"HALF v{__version__}")
    print(__description__)
    print(f"License: {__license__}")


def _route_command(args: argparse.Namespace) -> dict[str, object] | None:
    """Route to the appropriate handler."""
    if args.command == "version":
        _show_version()
        return None

    if args.command == "init":
        return _cmd_init(args)

    if args.command == "status":
        from half.half_sidecar import cmd_status

        return cmd_status()

    if args.command == "run-phase":
        from half.half_sidecar import cmd_run_phase

        return cmd_run_phase(args.phase, concept=getattr(args, "concept", ""))

    if args.command == "gate-check":
        from half.half_sidecar import cmd_gate_check

        return cmd_gate_check(args.phase)

    if args.command == "generate-mrp":
        from half.half_sidecar import cmd_generate_mrp

        return cmd_generate_mrp()

    if args.command == "voice":
        if args.voice_cmd == "stt":
            from half.half_sidecar import cmd_voice_stt

            return cmd_voice_stt(args.file)
        if args.voice_cmd == "tts":
            from half.half_sidecar import cmd_voice_tts

            return cmd_voice_tts(args.text)

    if args.command == "focalboard" and getattr(args, "fb_cmd", None) == "create":
        from half.half_sidecar import cmd_focalboard_create

        return cmd_focalboard_create()

    return {"error": f"Unknown command: {args.command}"}


def _cmd_init(args: argparse.Namespace) -> dict[str, object]:
    """Run genesis.sh to bootstrap a project."""
    # Search for genesis.sh in multiple possible locations
    candidate_paths = [
        Path(__file__).resolve().parent.parent.parent
        / "scripts"
        / "genesis.sh",  # editable install (src/scripts/)
        Path(__file__).resolve().parent.parent
        / "scripts"
        / "genesis.sh",  # editable install (half/scripts/)
        Path(__file__).resolve().parent
        / "data"
        / "scripts"
        / "genesis.sh",  # pip install (bundled package data)
        Path.cwd() / "scripts" / "genesis.sh",  # running from repo root
    ]

    genesis = None
    for p in candidate_paths:
        if p.exists():
            genesis = p
            break

    if genesis is None:
        return {
            "status": "error",
            "message": (
                "genesis.sh not found. Install HALF from the dev repo:\n"
                "  git clone https://github.com/iknowkungfubar/Hermes-Agentic-Lifecycle-Framework.git\n"
                "  cd Hermes-Agentic-Lifecycle-Framework\n"
                "  pip install -e .\n"
                "Then run 'half init' from the repo root."
            ),
        }

    repo_root = genesis.parent.parent  # scripts/genesis.sh -> scripts/ -> repo root
    target_dir = args.dir or args.project
    cmd = [
        "bash",
        str(genesis),
        "--project",
        args.project,
        "--mode",
        args.mode,
        "--dir",
        target_dir,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "project": args.project,
            "mode": args.mode,
            "directory": str(repo_root / target_dir),
            "output": result.stdout[-500:] if result.stdout else "",
            "errors": result.stderr[-500:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "genesis.sh timed out after 120s"}
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "bash not found — required to run genesis.sh",
        }


if __name__ == "__main__":
    main()
