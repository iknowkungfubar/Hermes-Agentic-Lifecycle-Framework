#!/usr/bin/env python3
"""HALF — Command-Line Interface.

Usage:
    half --help
    half init [--project NAME] [--mode full|prototype|patch|audit]
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
import sys
from pathlib import Path


def main() -> None:
    """Main CLI entrypoint for HALF."""
    parser = argparse.ArgumentParser(
        prog="half",
        description="Hermes Agentic Lifecycle Framework — Autonomous SDLC orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  half init --project my-app --mode full
  half status
  half run-phase phase-2
  half version
        """,
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show HALF version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize a new HALF project")
    init_parser.add_argument("--project", default="my-app", help="Project name")
    init_parser.add_argument(
        "--mode",
        default="full",
        choices=["full", "prototype", "patch", "audit"],
        help="Pipeline mode",
    )
    init_parser.add_argument("--dir", default="", help="Target directory")

    # status
    subparsers.add_parser("status", help="Show pipeline status")

    # run-phase
    run_parser = subparsers.add_parser("run-phase", help="Execute a pipeline phase")
    run_parser.add_argument("phase", help="Phase identifier (e.g., phase-1)")

    # gate-check
    gate_parser = subparsers.add_parser("gate-check", help="Run gate checks for a phase")
    gate_parser.add_argument("phase", help="Phase identifier (e.g., phase-1)")

    # generate-mrp
    subparsers.add_parser("generate-mrp", help="Generate Merge-Readiness Pack")

    # voice
    voice_parser = subparsers.add_parser("voice", help="Voice commands (STT/TTS)")
    voice_sub = voice_parser.add_subparsers(dest="voice_cmd")
    stt_parser = voice_sub.add_parser("stt", help="Transcribe audio file")
    stt_parser.add_argument("file", help="Path to audio file")
    tts_parser = voice_sub.add_parser("tts", help="Convert text to speech")
    tts_parser.add_argument("text", help="Text to speak")

    # focalboard
    fb_parser = subparsers.add_parser("focalboard", help="Focalboard Kanban integration")
    fb_sub = fb_parser.add_subparsers(dest="fb_cmd")
    fb_sub.add_parser("create", help="Create a Focalboard board")

    # version
    subparsers.add_parser("version", help="Show HALF version")

    args = parser.parse_args()

    if args.version or not args.command:
        _show_version()
        if not args.command:
            parser.print_help()
        return

    # Route commands
    try:
        result = _route_command(args)
        if result:
            print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _show_version() -> None:
    """Print HALF version information."""
    from src.half import __version__, __description__, __license__

    print(f"HALF v{__version__}")
    print(__description__)
    print(f"License: {__license__}")


def _route_command(args: argparse.Namespace) -> dict[str, object] | None:
    """Route parsed arguments to the appropriate handler.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Command result (dict for JSON output) or None.
    """
    if args.command == "version":
        _show_version()
        return None

    if args.command == "init":
        project = args.project
        mode = args.mode
        target_dir = args.dir or project
        msg = (
            f"To initialize a HALF project, run:\n"
            f"  ./scripts/genesis.sh --project {project} --mode {mode} --dir {target_dir}\n"
            f"Or use the Hermes skill:\n"
            f"  skill_view(name=\"half\")\n"
            f"  Then follow Phase 1: Discovery & Strategy"
        )
        print(msg)
        return None

    if args.command == "status":
        from src.half_sidecar import cmd_status
        return cmd_status()

    if args.command == "run-phase":
        from src.half_sidecar import cmd_run_phase
        return cmd_run_phase(args.phase)

    if args.command == "gate-check":
        from src.half_sidecar import cmd_gate_check
        return cmd_gate_check(args.phase)

    if args.command == "generate-mrp":
        from src.half_sidecar import cmd_generate_mrp
        return cmd_generate_mrp()

    if args.command == "voice":
        if args.voice_cmd == "stt":
            from src.half_sidecar import cmd_voice_stt
            return cmd_voice_stt(args.file)
        if args.voice_cmd == "tts":
            from src.half_sidecar import cmd_voice_tts
            return cmd_voice_tts(args.text)

    if args.command == "focalboard":
        if args.fb_cmd == "create":
            from src.half_sidecar import cmd_focalboard_create
            return cmd_focalboard_create()

    return {"error": f"Unknown command: {args.command}"}


if __name__ == "__main__":
    main()
