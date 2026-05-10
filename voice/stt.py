"""Speech-to-text using faster-whisper — no LLVM required."""

import numpy as np
import sounddevice as sd

import config

_model = None


def _load_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def record(duration: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
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
    model = _load_model()
    segments, _ = model.transcribe(audio, language="en")
    return " ".join(s.text for s in segments).strip()


def listen(duration: float = 5.0) -> str:
    return transcribe(record(duration))
