"""Text-to-speech via ElevenLabs with British female voice."""

import io
import pygame
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

import config

_client: ElevenLabs | None = None
_pygame_init = False


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    return _client


def _ensure_pygame():
    global _pygame_init
    if not _pygame_init:
        pygame.mixer.init(frequency=22050)
        _pygame_init = True


def speak(text: str, block: bool = True) -> None:
    """Convert text to speech and play it through the speakers."""
    client = _get_client()
    audio_bytes = client.text_to_speech.convert(
        voice_id=config.ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2",  # lowest latency
        voice_settings=VoiceSettings(
            stability=0.55,
            similarity_boost=0.80,
            style=0.15,
            use_speaker_boost=True,
        ),
        output_format="mp3_22050_32",
    )

    _ensure_pygame()
    buf = io.BytesIO(bytes(audio_bytes))
    pygame.mixer.music.load(buf)
    pygame.mixer.music.play()
    if block:
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
