"""HALF — LM Studio Instance Manager for AMD ROCm.

Manages LM Studio inference instances, load-balancing quantized models
across available AMD VRAM. Offloads complex tasks to cloud providers.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("half.lm_studio")


@dataclass
class ModelConfig:
    """Configuration for an LM Studio model."""

    name: str
    quantization: str = "Q4_K_M"
    context_length: int = 32768
    gpu_layers: int = -1  # All layers on GPU
    batch_size: int = 512


@dataclass
class InferenceProvider:
    """An inference provider with routing configuration."""

    name: str
    endpoint: str
    api_key_env: str = ""
    models: list[str] = field(default_factory=list)
    priority: int = 0  # Lower = preferred
    max_concurrent: int = 2


class LMStudioManager:
    """Manages local LM Studio instances for AMD ROCm inference.

    Routes tasks based on complexity:
    - Simple/small models → local AMD GPU (Q4/Q8 quantized)
    - Complex reasoning → cloud (OpenRouter, OpenCode, DeepSeek)
    """

    PROVIDERS = {
        "lmstudio": InferenceProvider("lmstudio", "http://127.0.0.1:1234/v1", "", priority=0, max_concurrent=2),
        "openrouter": InferenceProvider("openrouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY",
                                        ["openai/gpt-5.1", "anthropic/claude-sonnet-4"], priority=1),
        "opencode": InferenceProvider("opencode", "https://api.opencode.ai/v1", "OPENEAI_API_KEY",
                                      ["gpt-5.1-codex"], priority=1),
        "deepseek": InferenceProvider("deepseek", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY",
                                      ["deepseek-reasoner", "deepseek-chat"], priority=2),
    }

    def __init__(self) -> None:
        self.local_models: list[ModelConfig] = [
            ModelConfig("qwen2.5-coder:7b", "Q4_K_M"),
            ModelConfig("qwen2.5-coder:1.5b", "Q8_0", context_length=16384),
        ]

    def get_provider(self, role: str = "coder") -> InferenceProvider:
        """Get the appropriate provider for a given role.

        Args:
            role: Agent role (planner, coder, reviewer).

        Returns:
            The InferenceProvider to use.
        """
        # Complex planning → cloud
        if role == "planner":
            return self.PROVIDERS["openrouter"]
        # High-volume coding → local AMD
        if role == "coder":
            return self.PROVIDERS["lmstudio"]
        # Reviews → cheap/fast
        return self.PROVIDERS["deepseek"]

    def check_vram(self) -> dict[str, Any]:
        """Check available AMD VRAM via rocminfo.

        Returns:
            VRAM info dict.
        """
        try:
            result = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            import json
            data = json.loads(result.stdout) if result.stdout else {}
            return {
                "available": True,
                "info": data,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return {"available": False, "error": "rocm-smi not available"}

    def select_model(self, task_complexity: str = "medium") -> ModelConfig:
        """Select the best local model for a given task complexity.

        Args:
            task_complexity: 'low', 'medium', or 'high'.

        Returns:
            ModelConfig for the selected model.
        """
        if task_complexity == "low":
            return self.local_models[1]  # 1.5B Q8
        return self.local_models[0]  # 7B Q4

    def get_endpoint(self, provider: str = "lmstudio") -> str:
        """Get the API endpoint for a provider.

        Args:
            provider: Provider name.

        Returns:
            API endpoint URL.
        """
        p = self.PROVIDERS.get(provider)
        return p.endpoint if p else "http://127.0.0.1:1234/v1"
