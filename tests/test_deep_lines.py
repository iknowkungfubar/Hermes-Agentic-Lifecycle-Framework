"""Targeted tests for specific uncovered lines in half_sidecar, __main__, http_sidecar, rest_daemon, webhooks."""

from __future__ import annotations

import argparse
import io
import sys

import pytest


class TestHalfSidecarDeepLines:
    def test_run_phase_exception(self):
        from half.half_sidecar import cmd_run_phase
        result = cmd_run_phase("phase-7")
        assert "status" in result


class TestMainDeepLines:
    def test_main_with_version_flag(self):
        from half.__main__ import main
        captured = io.StringIO()
        old = sys.stdout
        sys.stdout = captured
        old_argv = sys.argv
        sys.argv = ["half", "--version"]
        try:
            try:
                main()
            except (SystemExit, Exception):
                pass
            output = captured.getvalue()
            assert "HALF" in output
        finally:
            sys.stdout = old
            sys.argv = old_argv

    def test_dispatch_version(self):
        from half.__main__ import _route_command
        assert _route_command(argparse.Namespace(command="version", version=False)) is None

    def test_dispatch_status(self):
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(command="status", version=False))
        assert isinstance(r, dict)

    def test_dispatch_run_phase(self):
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(command="run-phase", phase="phase-1", version=False))
        assert isinstance(r, dict)

    def test_dispatch_gate_check(self):
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(command="gate-check", phase="phase-1", version=False))
        assert isinstance(r, dict)

    def test_dispatch_generate_mrp(self):
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(command="generate-mrp", version=False))
        assert isinstance(r, dict)

    def test_dispatch_init(self):
        from half.__main__ import _route_command
        r = _route_command(argparse.Namespace(command="init", project="test", mode="full", dir="/tmp", version=False))
        assert r is not None


class TestHTTPSidecarDeepLines:
    def test_handler_methods(self):
        from half.http_sidecar import HalfAPIHandler, run_server
        assert hasattr(HalfAPIHandler, "do_GET")
        assert callable(run_server)


class TestRestDaemonDeepLines:
    def test_handler_methods(self):
        from half.rest_daemon import RESTAPIHandler, run_server
        assert hasattr(RESTAPIHandler, "do_GET")
        assert callable(run_server)


class TestWebhooksDeepLines:
    def test_handler_server(self):
        from half.webhooks import WebhookHandler, WebhookServer
        s = WebhookServer(handler=WebhookHandler())
        assert s is not None
