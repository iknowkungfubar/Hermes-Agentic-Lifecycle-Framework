"""HALF 1.5 — VRAM Monitor & Resource Tracking.

Tracks AMD GPU VRAM consumption via rocminfo. Assigns priority to
voice engines (Whisper.cpp/Piper) and throttles background agents
through LM Studio instance scaling.

Based on the HALF 1.5 doctrine's 'Intelligent Resource Allocation' spec.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("half.vram_monitor")


@dataclass
class GPUInfo:
    """Information about an AMD GPU."""

    device_id: str = ""
    device_name: str = ""
    vram_total_mb: int = 0
    vram_free_mb: int = 0
    vram_used_mb: int = 0
    temperature_c: float = 0.0
    driver_version: str = ""


@dataclass
class ResourceAllocation:
    """Resource allocation decision."""

    priority_queue: list[str] = field(default_factory=list)
    throttled_agents: list[str] = field(default_factory=list)
    vram_available_mb: int = 0
    recommended_max_agents: int = 0
    should_offload: bool = False


class VRAMMonitor:
    """Monitors AMD GPU VRAM and manages resource allocation.

    Gives highest priority to real-time voice engines (Whisper.cpp/Piper).
    Queues background coding agents through LM Studio instance scaling.
    Offloads complex tasks to cloud when VRAM runs low.

    Usage:
        monitor = VRAMMonitor()
        gpu_info = monitor.get_gpu_info()
        allocation = monitor.get_allocation(
            vram_needed_voice=512,   # MB for voice engines
            vram_needed_coder=2048,  # MB per coding agent
            num_agents=4,
        )
    """

    def __init__(self) -> None:
        self._gpu_info: GPUInfo | None = None

    def get_gpu_info(self) -> GPUInfo:
        """Query AMD GPU state via rocminfo.

        Returns:
            GPUInfo with VRAM usage. Falls back to estimated values.
        """
        info = GPUInfo()

        try:
            # Try rocminfo
            result = subprocess.run(
                ["rocminfo"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if "Device ID:" in line:
                        info.device_id = line.split(":")[-1].strip()
                    if "Marketing Name:" in line:
                        info.device_name = line.split(":")[-1].strip()
                    if "Driver:" in line:
                        info.driver_version = line.split(":")[-1].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.info("VRAM: rocminfo not available — estimating GPU state")

        # Try reading from /sys/class/drm/ for AMD GPU
        try:
            import glob
            drm_paths = glob.glob("/sys/class/drm/card*/device/mem_info_vram_total")
            if drm_paths:
                total_path = drm_paths[0]
                free_path = total_path.replace("vram_total", "vram_free")
                try:
                    with open(total_path) as f:
                        info.vram_total_mb = int(f.read().strip()) // (1024 * 1024)
                    with open(free_path) as f:
                        info.vram_free_mb = int(f.read().strip()) // (1024 * 1024)
                    info.vram_used_mb = info.vram_total_mb - info.vram_free_mb
                except (ValueError, OSError):
                    pass
        except Exception:
            pass

        # Try nvidia-smi as fallback (NVIDIA GPUs)
        if info.vram_total_mb == 0:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.total,memory.free,name",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(",")
                    if len(parts) >= 3:
                        info.vram_total_mb = int(parts[0].strip())
                        info.vram_free_mb = int(parts[1].strip())
                        info.vram_used_mb = info.vram_total_mb - info.vram_free_mb
                        info.device_name = parts[2].strip()
            except Exception:
                pass

        # Default values if nothing detected
        if info.vram_total_mb == 0:
            info.vram_total_mb = 24576  # Assume 24GB (RX 7900 XTX)
            info.vram_free_mb = 16384
            info.vram_used_mb = info.vram_total_mb - info.vram_free_mb
            info.device_name = "AMD Radeon RX 7900 XTX (estimated)"

        self._gpu_info = info
        return info

    def get_allocation(
        self,
        vram_needed_voice: int = 512,
        vram_needed_coder: int = 2048,
        num_agents: int = 1,
    ) -> ResourceAllocation:
        """Calculate resource allocation for agents.

        Args:
            vram_needed_voice: VRAM needed for voice engines (MB).
            vram_needed_coder: VRAM needed per coding agent (MB).
            num_agents: Number of desired agents.

        Returns:
            ResourceAllocation with priority and throttling decisions.
        """
        gpu = self.get_gpu_info()
        alloc = ResourceAllocation(
            vram_available_mb=gpu.vram_free_mb,
        )

        # Always reserve VRAM for voice engines (highest priority)
        vram_after_voice = gpu.vram_free_mb - vram_needed_voice
        if vram_after_voice < 0:
            logger.warning("VRAM: Insufficient memory for voice engines!")
            alloc.should_offload = True
            alloc.priority_queue = ["voice"]
            return alloc

        # Calculate how many coding agents can run
        max_coders = vram_after_voice // vram_needed_coder
        alloc.recommended_max_agents = max(1, max_coders)

        # Throttle if more agents requested than available
        if num_agents > max_coders:
            alloc.throttled_agents = [f"coder-{i}" for i in range(max_coders, num_agents)]
            alloc.should_offload = num_agents > max_coders * 2
            logger.info("VRAM: Throttling %d agents, offload=%s",
                        len(alloc.throttled_agents), alloc.should_offload)

        alloc.priority_queue = ["voice"] + [f"coder-{i}" for i in range(min(num_agents, max_coders))]
        return alloc

    def to_dict(self) -> dict[str, Any]:
        """Get VRAM state as a dict for GUI display.

        Returns:
            Dict with VRAM metrics.
        """
        gpu = self.get_gpu_info()
        return {
            "device": gpu.device_name,
            "vram_total_mb": gpu.vram_total_mb,
            "vram_used_mb": gpu.vram_used_mb,
            "vram_free_mb": gpu.vram_free_mb,
            "usage_percent": round(gpu.vram_used_mb / max(1, gpu.vram_total_mb) * 100, 1),
            "driver": gpu.driver_version or "not detected",
        }
