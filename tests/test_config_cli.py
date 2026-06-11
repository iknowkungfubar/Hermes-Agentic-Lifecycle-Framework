"""Tests for HALF config, providers, and CLI modules."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class TestHalfConfig:
    """Test the central configuration module."""

    def test_get_half_home_default(self):
        """Default HALF_HOME should be .hale in cwd."""
        from half.config import get_half_home

        home = get_half_home()
        assert str(home).endswith(".hale")

    def test_get_half_home_env_var(self):
        """HALF_HOME env var should override default."""
        from half.config import get_half_home

        os.environ["HALF_HOME"] = "/tmp/half-test"
        try:
            home = get_half_home()
            assert str(home) == "/tmp/half-test"
        finally:
            del os.environ["HALF_HOME"]

    def test_ensure_dirs_creates_all(self):
        """ensure_dirs should create all required directories."""
        from half.config import ensure_dirs

        with tempfile.TemporaryDirectory() as tmp:
            original_cwd = Path.cwd()
            os.chdir(tmp)
            os.environ["HALF_HOME"] = str(Path(tmp) / ".hale")
            try:
                ensure_dirs()
                assert (Path(tmp) / ".hale" / "artifacts" / "phase-1").exists()
                assert (Path(tmp) / ".hale" / "state" / "checkpoints").exists()
                assert (Path(tmp) / ".hale" / "agent-mail").exists()
                assert (Path(tmp) / ".hale" / "metrics").exists()
                assert (Path(tmp) / ".hale" / "logs").exists()
                assert (Path(tmp) / ".hale" / "security").exists()
            finally:
                os.chdir(original_cwd)
                del os.environ["HALF_HOME"]

    def test_config_constants_are_strings(self):
        """All config constants should be non-empty strings."""
        import half.config as cfg

        attrs = [a for a in dir(cfg) if a.isupper() and not a.startswith("_")]
        for attr in attrs:
            val = getattr(cfg, attr)
            assert isinstance(val, str), f"{attr} should be str, got {type(val)}"
            assert val, f"{attr} should not be empty"


class TestProviderRouter:
    """Test the inference provider switching system."""

    def test_default_provider(self):
        """Default provider should be openrouter."""
        from half.providers import ProviderRouter

        router = ProviderRouter()
        assert router.provider == "openrouter"

    def test_get_model_for_role(self):
        """Getting a model for a role should return a valid mapping."""
        from half.providers import ProviderRouter

        router = ProviderRouter(provider="openrouter")
        model = router.get_model("planner")
        assert model.role == "planner"
        assert model.provider == "openrouter"
        assert model.model

    def test_get_model_for_unknown_role_falls_back(self):
        """Unknown role should fall back to first available mapping."""
        from half.providers import ProviderRouter

        router = ProviderRouter(provider="deepseek")
        model = router.get_model("nonexistent-role")
        assert model is not None  # Falls back to first

    def test_list_providers(self):
        """Listing providers should return all known providers."""
        from half.providers import ProviderRouter

        providers = ProviderRouter.list_providers()
        assert "opencode" in providers
        assert "openrouter" in providers
        assert "deepseek" in providers
        assert "lmstudio" in providers
        assert "custom" in providers

    def test_list_models(self):
        """Listing models should return dicts with role, provider, model."""
        from half.providers import ProviderRouter

        router = ProviderRouter(provider="lmstudio")
        models = router.list_models()
        assert len(models) > 0
        assert "role" in models[0]
        assert "provider" in models[0]
        assert "model" in models[0]

    def test_get_endpoint(self):
        """Getting endpoint should return a URL."""
        from half.providers import ProviderRouter

        router = ProviderRouter(provider="deepseek")
        endpoint = router.get_endpoint("coder")
        assert endpoint.startswith("http")

    def test_get_api_key_from_env(self):
        """Getting API key should read from env var."""
        from half.providers import ProviderRouter

        router = ProviderRouter(provider="openrouter")
        key = router.get_api_key("planner")
        # Should be empty since env var is not set
        assert isinstance(key, str)

    def test_custom_provider_config(self):
        """Loading from a custom config file should work."""
        import json

        from half.providers import ProviderRouter

        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "providers.json"
            config_file.write_text(json.dumps({
                "models": [
                    {"role": "coder", "provider": "custom", "model": "my-model", "endpoint": "http://localhost:8080/v1"}
                ]
            }))
            router = ProviderRouter(provider="custom", config_file=str(config_file))
            model = router.get_model("coder")
            assert model.model == "my-model"
            assert model.endpoint == "http://localhost:8080/v1"


class TestHalfCLI:
    """Test the HALF CLI entry point."""

    def test_version_output(self):
        """half version should print version info."""
        from half import __version__
        assert __version__ == "1.0.0"

    def test_import_main(self):
        """The main function should be importable."""
        from half.__main__ import main
        assert main is not None

    def test_route_init_command(self):
        """init command should be routable."""
        import argparse

        from half.__main__ import _route_command

        args = argparse.Namespace(command="init", project="test-half", mode="full", dir="/tmp/test-half-install")
        result = _route_command(args)
        assert result is not None
        assert isinstance(result, dict)
        assert "project" in result
        assert result["project"] == "test-half"

    def test_route_unknown_command(self):
        """Unknown commands should return error dict."""
        import argparse

        from half.__main__ import _route_command

        args = argparse.Namespace(command="nonexistent", fb_cmd="")
        result = _route_command(args)
        assert isinstance(result, dict)
        assert "error" in result


class TestHalfInit:
    """Test the HALF package init."""

    def test_version_constant(self):
        """Version constant should exist."""
        import half
        assert half.__version__ == "1.0.0"

    def test_license_constant(self):
        """License constant should exist."""
        import half
        assert half.__license__ == "MIT"

    def test_python_version_check(self):
        """Python version check should pass on 3.13+."""
        import sys
        assert sys.version_info >= (3, 13)
