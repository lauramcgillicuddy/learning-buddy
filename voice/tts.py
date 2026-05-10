"""Text-to-speech — supports ElevenLabs and Google Cloud TTS."""

import io
import pygame
import config

_pygame_init = False


def _ensure_pygame():
    global _pygame_init
    if not _pygame_init:
        pygame.mixer.init(frequency=22050)
        _pygame_init = True


def _speak_elevenlabs(text: str) -> None:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    audio_bytes = client.text_to_speech.convert(
        voice_id=config.ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.55,
            similarity_boost=0.80,
            style=0.15,
            use_speaker_boost=True,
        ),
        output_format="mp3_22050_32",
    )
    _play_bytes(bytes(audio_bytes))


def _speak_google(text: str) -> None:
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        # en-GB-Journey-F is warm, natural RP British female
        language_code="en-GB",
        name=config.GOOGLE_TTS_VOICE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=1.0,
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    _play_bytes(response.audio_content)


def _play_bytes(audio: bytes) -> None:
    _ensure_pygame()
    buf = io.BytesIO(audio)
    pygame.mixer.music.load(buf)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def speak(text: str) -> None:
    match config.TTS_PROVIDER.lower():
        case "google":
            _speak_google(text)
        case "elevenlabs":
            _speak_elevenlabs(text)
        case other:
            raise ValueError(f"Unknown TTS_PROVIDER '{other}'. Supported: elevenlabs, google")
