"""HALF — Inference Provider Switcher.

Maps abstract model roles to concrete provider/model pairs.
Eliminates hardcoded model names — users configure once and
the framework routes all inference through the selected provider.

Supported providers:
  - opencode: OpenCode.ai (Zen/Go models)
  - openrouter: OpenRouter request-routing
  - deepseek: DeepSeek API
  - lmstudio: Local LM Studio (AMD ROCm via llama.cpp)
  - custom: User-defined OpenAI-compatible endpoint
"""

from __future__ import annotations


def _redact(value: str | None, show_last: int = 4) -> str:
    """Redact sensitive values, showing only last N characters."""
    if not value:
        return "***"
    if len(value) <= show_last + 4:
        return "***" + value[-show_last:]
    return value[:4] + "..." + value[-show_last:]


import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("half.providers")


@dataclass
class ModelMapping:
    """A mapping from HALF role to a concrete model."""

    role: str  # planner, coder, reviewer
    provider: str  # opencode, openrouter, deepseek, lmstudio, custom
    model: str  # actual model name/ID
    api_key: str = ""  # env var name, e.g., "OPENROUTER_API_KEY"
    endpoint: str = ""  # custom endpoint URL


DEFAULT_CONFIGS: dict[str, list[ModelMapping]] = {
    "opencode": [
        ModelMapping("planner", "opencode", "gpt-5.1-codex", "OPENEAI_API_KEY"),
        ModelMapping("coder", "opencode", "gpt-5.1-codex", "OPENEAI_API_KEY"),
        ModelMapping("reviewer", "opencode", "gpt-5.1-codex", "OPENEAI_API_KEY"),
    ],
    "openrouter": [
        ModelMapping("planner", "openrouter", "openai/gpt-5.1", "OPENROUTER_API_KEY"),
        ModelMapping(
            "coder", "openrouter", "anthropic/claude-sonnet-4", "OPENROUTER_API_KEY"
        ),
        ModelMapping(
            "reviewer", "openrouter", "google/gemini-2.5-pro", "OPENROUTER_API_KEY"
        ),
    ],
    "deepseek": [
        ModelMapping("planner", "deepseek", "deepseek-reasoner", "DEEPSEEK_API_KEY"),
        ModelMapping("coder", "deepseek", "deepseek-chat", "DEEPSEEK_API_KEY"),
        ModelMapping("reviewer", "deepseek", "deepseek-chat", "DEEPSEEK_API_KEY"),
    ],
    "lmstudio": [
        ModelMapping(
            "planner", "lmstudio", "qwen2.5-coder:7b", "", "http://127.0.0.1:1234/v1"
        ),
        ModelMapping(
            "coder", "lmstudio", "qwen2.5-coder:7b", "", "http://127.0.0.1:1234/v1"
        ),
        ModelMapping(
            "reviewer", "lmstudio", "qwen2.5-coder:7b", "", "http://127.0.0.1:1234/v1"
        ),
    ],
    "custom": [
        ModelMapping(
            "planner", "custom", "", "CUSTOM_API_KEY", "http://127.0.0.1:8000/v1"
        ),
        ModelMapping(
            "coder", "custom", "", "CUSTOM_API_KEY", "http://127.0.0.1:8000/v1"
        ),
        ModelMapping(
            "reviewer", "custom", "", "CUSTOM_API_KEY", "http://127.0.0.1:8000/v1"
        ),
    ],
}


class ProviderRouter:
    """Routes HALF model requests to the configured provider.

    Usage:
        router = ProviderRouter(provider="openrouter")
        planner_model = router.get_model("planner")
        # Returns: ModelMapping(role="planner", provider="openrouter", model="openai/gpt-5.1", ...)
    """

    def __init__(
        self,
        provider: str = "openrouter",
        config_file: str | Path = "",
    ):
        self.provider = provider
        self._mappings: list[ModelMapping] = []

        if config_file:
            self._load_config(Path(config_file))
        elif provider in DEFAULT_CONFIGS:
            self._mappings = list(DEFAULT_CONFIGS[provider])
            logger.info("ProviderRouter: using default config for '%s'", provider)
        else:
            logger.warning(
                "ProviderRouter: unknown provider '%s', falling back to openrouter",
                provider,
            )
            self._mappings = list(DEFAULT_CONFIGS["openrouter"])

    def _load_config(self, config_file: Path) -> None:
        """Load provider config from a JSON file."""
        if not config_file.exists():
            logger.warning("Provider config not found: %s", config_file)
            self._mappings = list(
                DEFAULT_CONFIGS.get(self.provider, DEFAULT_CONFIGS["openrouter"])
            )
            return

        try:
            data = json.loads(config_file.read_text())
            mappings = []
            for entry in data.get("models", []):
                mappings.append(
                    ModelMapping(
                        role=entry.get("role", "coder"),
                        provider=entry.get("provider", self.provider),
                        model=entry.get("model", ""),
                        api_key=entry.get("api_key", ""),
                        endpoint=entry.get("endpoint", ""),
                    )
                )
            if mappings:
                self._mappings = mappings
                logger.info(
                    "Loaded %d model mappings from %s", len(mappings), config_file
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.exception("Failed to load provider config: %s", e)
            self._mappings = list(
                DEFAULT_CONFIGS.get(self.provider, DEFAULT_CONFIGS["openrouter"])
            )

    def get_model(self, role: str = "coder") -> ModelMapping:
        """Get the model mapping for a given role.

        Args:
            role: Agent role (planner, coder, reviewer).

        Returns:
            ModelMapping for the requested role.

        Raises:
            ValueError: If no mapping found for the role.
        """
        for m in self._mappings:
            if m.role == role:
                return m
        # Fallback: return first available
        if self._mappings:
            logger.warning(
                "No mapping for role '%s', using first available: %s/%s",
                role,
                self._mappings[0].provider,
                self._mappings[0].model,
            )
            return self._mappings[0]
        msg = f"No model mappings configured for provider '{self.provider}'"
        raise ValueError(msg)

    def get_api_key(self, role: str = "coder") -> str:
        """Get the API key for a given role, resolving from env vars.

        Args:
            role: Agent role.

        Returns:
            API key string, or empty string if not configured.
        """
        mapping = self.get_model(role)
        if not mapping.api_key:
            return ""
        key = os.environ.get(mapping.api_key, "")
        if not key:
            logger.warning(
                "API key env var name not set for role '%s'",
                role,  # mapping.api_key is the env-var NAME, not the secret value
            )
        return key

    def get_endpoint(self, role: str = "coder") -> str:
        """Get the API endpoint for a given role.

        Args:
            role: Agent role.

        Returns:
            API endpoint URL.
        """
        mapping = self.get_model(role)
        if mapping.endpoint:
            return mapping.endpoint

        defaults = {
            "opencode": "https://api.opencode.ai/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "lmstudio": "http://127.0.0.1:1234/v1",
            "custom": "http://127.0.0.1:8000/v1",
        }
        return defaults.get(mapping.provider, defaults["openrouter"])

    def list_models(self) -> list[dict[str, str]]:
        """List all configured model mappings.

        Returns:
            List of dicts with role, provider, model.
        """
        return [
            {"role": m.role, "provider": m.provider, "model": m.model}
            for m in self._mappings
        ]

    @staticmethod
    def list_providers() -> list[str]:
        """List all available provider names.

        Returns:
            List of provider names.
        """
        return list(DEFAULT_CONFIGS.keys())
