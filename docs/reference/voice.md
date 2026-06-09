# Voice Engine

The **Voice Engine** provides speech-to-text (STT) and text-to-speech (TTS)
capabilities for air-gapped voice interaction with the Command Center.

## Components

### Speech-to-Text: Whisper.cpp

- Runs locally on CPU or AMD ROCm (RX 7900 XTX)
- Models auto-downloaded from HuggingFace
- Supports 99+ languages

### Text-to-Speech: Piper

- Local neural TTS engine (no cloud dependency)
- Voice models: en_US-less-medium (default)
- Fast inference on CPU

## CLI Usage

```bash
# Transcribe audio file
half voice stt command.wav

# Convert text to speech
half voice tts "Deploy pipeline ready for review"
```

## API Usage

```python
from src.half_voice import VoiceEngine

engine = VoiceEngine()
text = engine.transcribe("recording.wav")
engine.speak("Status: all gates passed")
```

## Browser Fallback

When native engines aren't installed, the Tauri GUI falls back to
the browser's Web Speech API for TTS and MediaRecorder for STT.
