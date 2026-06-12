"""
HALF — Voice Module: Speech-to-Text & Text-to-Speech

Wraps local Whisper.cpp (STT) and Piper (TTS) engines
for private, air-gapped voice interaction with the Command Center.

Hardware-accelerated via AMD ROCm on RDNA3 (RX 7900 XTX).

Usage:
    from half.half_voice import VoiceEngine
    engine = VoiceEngine()
    text = engine.transcribe("input.wav")   # STT
    engine.speak("Hello, Commander")         # TTS
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from half import config

logger = logging.getLogger("half.voice")


class VoiceEngine:
    """Speech-to-Text and Text-to-Speech engine.

    Uses Whisper.cpp for STT (runs locally on AMD ROCm).
    Uses Piper for TTS (runs locally on CPU/ROCm).

    Falls back gracefully if engines aren't installed.
    """

    def __init__(
        self,
        whisper_model: str = "ggml-tiny.en.bin",
        whisper_exec: str = "",
        piper_exec: str = "",
        piper_voice: str = "",
        models_dir: str | Path = "",
        device: str = "auto",
    ):
        if not models_dir:
            models_dir = Path(__file__).resolve().parent.parent.parent.parent / ".whisper" / "models"
        self.models_dir = Path(models_dir)
        self.whisper_model = whisper_model
        self.whisper_exec = whisper_exec or self._find_whisper()
        self.piper_exec = piper_exec or self._find_piper()
        if not piper_voice:
            piper_voice = str(Path(__file__).resolve().parent.parent.parent.parent / ".piper" / "voices" / "en_US-lessac-medium.onnx")
        self.piper_voice = piper_voice
        self.device = device

        self._stt_available = bool(self.whisper_exec)
        self._tts_available = bool(self.piper_exec)

        if not self._stt_available:
            logger.info(
                "Whisper.cpp not found — STT disabled (install: https://github.com/ggerganov/whisper.cpp)"
            )
        if not self._tts_available:
            logger.info(
                "Piper not found — TTS disabled (install: https://github.com/rhasspy/piper)"
            )

    def _find_whisper(self) -> str:
        """Find whisper.cpp executable."""
        candidates = ["whisper-cli", "whisper", "./whisper", "main"]
        for cmd in candidates:
            path = self._which(cmd)
            if path:
                return path
        # Check common locations
        whisper_dirs = [
            Path(__file__).resolve().parent.parent.parent.parent / ".whisper" / "build" / "bin",
            Path(__file__).resolve().parent.parent.parent.parent / ".whisper",
            Path("/usr/local/bin"),
            Path(os.path.expanduser("~/.whisper")),
        ]
        for d in whisper_dirs:
            for name in ["whisper-cli", "main", "whisper"]:
                p = d / name
                if p.exists() and os.access(str(p), os.X_OK):
                    return str(p)
        return ""

    def _find_piper(self) -> str:
        """Find piper executable."""
        candidates = ["piper", "piper-tts"]
        for cmd in candidates:
            path = self._which(cmd)
            if path:
                return path
        piper_dirs = [
            Path(__file__).resolve().parent.parent.parent.parent / ".piper" / "build" / "piper",
            Path("/usr/local/bin"),
            Path(os.path.expanduser("~/.piper")),
        ]
        for d in piper_dirs:
            p = d if d.name == "piper" and d.parent.name == "piper" else d / "piper"
            if p.exists() and os.access(str(p), os.X_OK):
                return str(p)
        return ""

    @staticmethod
    def _which(cmd: str) -> str:
        """Check if a command exists in PATH."""
        try:
            result = subprocess.run(
                ["which", cmd], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return ""

    # ─── Speech-to-Text ───────────────────────────────────────────────────

    def transcribe(self, audio_path: str | Path, language: str = "en") -> str:
        """Transcribe an audio file to text using Whisper.cpp.

        Args:
            audio_path: Path to audio file (wav, mp3, etc.).
            language: Language code (default: en).

        Returns:
            Transcribed text.

        Raises:
            RuntimeError: If STT is not available.
        """
        if not self._stt_available:
            msg = (
                "STT unavailable — Whisper.cpp not found. "
                "Install from https://github.com/ggerganov/whisper.cpp"
            )
            raise RuntimeError(msg)

        audio_path = Path(audio_path)
        if not audio_path.exists():
            msg = f"Audio file not found: {audio_path}"
            raise FileNotFoundError(msg)

        cmd = [
            self.whisper_exec,
            "-m",
            str(self.models_dir / self.whisper_model),
            "-f",
            str(audio_path),
            "-l",
            language,
            "-oj",  # JSON output
        ]

        if self.device == "rocm":
            cmd.extend(["--gpu", "1"])

        logger.info("Transcribing %s...", audio_path.name)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.warning("Whisper stderr: %s", result.stderr[:500])
                return "[transcription failed]"

            # Parse JSON output
            try:
                data_json = json.loads(result.stdout)
                if isinstance(data_json, dict):
                    text: str = data_json.get("text", "")
                    return text
                if isinstance(data_json, list):
                    parts: list[str] = []
                    for s in data_json:
                        if isinstance(s, dict):
                            parts.append(s.get("text", ""))
                    return " ".join(parts)
            except json.JSONDecodeError:
                pass

            # Fallback: return raw stdout
            text_fallback: str = result.stdout.strip()
            return text_fallback

        except subprocess.TimeoutExpired:
            msg = "Whisper transcription timed out"
            raise RuntimeError(msg)

    def transcribe_microphone(self, duration_seconds: int = 5) -> str:
        """Record from microphone and transcribe.

        Requires 'arecord' (Linux) or 'sox' installed.

        Args:
            duration_seconds: Recording duration.

        Returns:
            Transcribed text.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            # Record using arecord (Linux)
            record_cmd = [
                "arecord",
                "-f",
                "S16_LE",
                "-r",
                "16000",
                "-c",
                "1",
                "-d",
                str(duration_seconds),
                temp_path,
            ]
            subprocess.run(record_cmd, check=True, timeout=duration_seconds + 5)

            # Transcribe
            return self.transcribe(temp_path)
        except subprocess.TimeoutExpired:
            msg = "Microphone recording timed out"
            raise RuntimeError(msg)
        except subprocess.CalledProcessError as e:
            msg = f"Recording failed: {e}"
            raise RuntimeError(msg)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # ─── Text-to-Speech ───────────────────────────────────────────────────

    def speak(self, text: str, output_path: str | Path = "") -> str:
        """Convert text to speech using Piper.

        Args:
            text: Text to speak.
            output_path: Optional output WAV path. Auto-temp if empty.

        Returns:
            Path to generated audio file.

        Raises:
            RuntimeError: If TTS is not available.
        """
        if not self._tts_available:
            msg = (
                "TTS unavailable — Piper not found. "
                "Install from https://github.com/rhasspy/piper"
            )
            raise RuntimeError(msg)

        if not output_path:
            output_path = str(Path(tempfile.mkdtemp()) / "output.wav")

        cmd = [
            self.piper_exec,
            "--model",
            self.piper_voice if Path(self.piper_voice).is_absolute() else str(self.models_dir / self.piper_voice),
            "--output-file",
            output_path,
        ]

        logger.info("Generating TTS for %d chars...", len(text))

        try:
            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=60,
            )
            if result.returncode != 0:
                stderr_text = result.stderr[:500].decode("utf-8", errors="replace")
                logger.warning("Piper stderr: %s", stderr_text)
                stderr_short = result.stderr[:200].decode("utf-8", errors="replace")
                msg = f"TTS generation failed: {stderr_short}"
                raise RuntimeError(msg)

            logger.info("TTS output: %s", output_path)
            return str(output_path)

        except subprocess.TimeoutExpired:
            msg = "Piper TTS timed out"
            raise RuntimeError(msg)

    def speak_async(self, text: str) -> None:
        """Speak text asynchronously (fire-and-forget).

        Args:
            text: Text to speak.
        """
        import threading

        def _speak_wrapper(t: str) -> None:
            try:
                self.speak(t)
            except Exception as exc:
                logger.debug("Async TTS skipped: %s", exc)

        thread = threading.Thread(target=_speak_wrapper, args=(text,), daemon=True)
        thread.start()

    # ─── Model Management ─────────────────────────────────────────────────

    def download_model(self, model_type: str = "whisper") -> bool:
        """Download voice models.

        Args:
            model_type: 'whisper' or 'piper'.

        Returns:
            True if downloaded successfully.
        """
        if model_type == "whisper":
            url = (
                f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
                f"{self.whisper_model}"
            )
            target = self.models_dir / self.whisper_model
        elif model_type == "piper":
            url = (
                f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/"
                f"{self.piper_voice}"
            )
            target = self.models_dir / self.piper_voice
        else:
            msg = f"Unknown model type: {model_type}"
            raise ValueError(msg)

        if target.exists():
            logger.info("Model already exists: %s", target)
            return True

        logger.info("Downloading %s from %s...", model_type, url)
        try:
            subprocess.run(
                [
                    "curl",
                    "-L",
                    "--connect-timeout",
                    "5",
                    "--max-time",
                    "30",
                    "-o",
                    str(target),
                    url,
                ],
                check=True,
                timeout=60,
            )
            logger.info("Downloaded: %s", target)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.exception("Download failed: %s", e)
            return False

    @property
    def is_available(self) -> dict[str, bool]:
        """Check if voice engines are available.

        Returns:
            Dict with 'stt' and 'tts' availability.
        """
        return {
            "stt": self._stt_available,
            "tts": self._tts_available,
        }
