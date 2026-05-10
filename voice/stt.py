"""Speech-to-text using local Whisper model."""

import io
import numpy as np
import sounddevice as sd
import whisper

import config

_model: whisper.Whisper | None = None


def _load_model() -> whisper.Whisper:
    global _model
    if _model is None:
        _model = whisper.load_model(config.WHISPER_MODEL)
    return _model


def record(duration: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    """Record audio from the default microphone for the given duration."""
    print(f"[Listening for {duration:.0f}s...]")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio.flatten()


def transcribe(audio: np.ndarray) -> str:
    """Transcribe a numpy float32 audio array to text."""
    model = _load_model()
    result = model.transcribe(audio, language="en", fp16=False)
    return result["text"].strip()


def listen(duration: float = 5.0) -> str:
    """Record and transcribe in one call."""
    return transcribe(record(duration))
