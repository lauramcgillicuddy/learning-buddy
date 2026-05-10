"""Text-to-speech — supports ElevenLabs and Google Cloud TTS.

Audio is synthesised as 16 kHz mono WAV so it can be pushed directly to
Reachy Mini's speaker without any additional decoding library.
"""

import io
import wave
import struct
import numpy as np
import config

_pygame_init = False


def _ensure_pygame():
    global _pygame_init
    if not _pygame_init:
        import pygame
        pygame.mixer.init(frequency=16000)
        _pygame_init = True


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1, sampwidth: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _synthesize_elevenlabs(text: str) -> bytes:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    # pcm_16000 = raw 16-bit signed PCM at 16 kHz, mono
    pcm = bytes(client.text_to_speech.convert(
        voice_id=config.ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.55,
            similarity_boost=0.80,
            style=0.15,
            use_speaker_boost=True,
        ),
        output_format="pcm_16000",
    ))
    return _pcm_to_wav(pcm, sample_rate=16000)


def _synthesize_google(text: str) -> bytes:
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB",
        name=config.GOOGLE_TTS_VOICE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        speaking_rate=1.0,
        pitch=1.0,
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content  # already WAV (LINEAR16)


def synthesize(text: str) -> bytes:
    """Return 16 kHz mono WAV bytes for the given text."""
    match config.TTS_PROVIDER.lower():
        case "google":
            return _synthesize_google(text)
        case "elevenlabs":
            return _synthesize_elevenlabs(text)
        case other:
            raise ValueError(f"Unknown TTS_PROVIDER '{other}'. Supported: elevenlabs, google")


def _play_local(wav_bytes: bytes) -> None:
    import pygame
    _ensure_pygame()
    buf = io.BytesIO(wav_bytes)
    pygame.mixer.music.load(buf)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def speak(text: str) -> None:
    wav_bytes = synthesize(text)

    from reachy import controller
    if controller.is_connected():
        controller.play_audio(wav_bytes)
    else:
        _play_local(wav_bytes)
