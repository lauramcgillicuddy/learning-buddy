import os
from dotenv import load_dotenv

load_dotenv()

# --- AI provider ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")  # "anthropic" or "openai"

# Only the key for your chosen provider needs to be set
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "claude":    "claude-sonnet-4-6",
    "openai":    "gpt-4o",
    "gpt":       "gpt-4o",
    "gemini":    "gemini-2.0-flash",
    "google":    "gemini-2.0-flash",
}
AI_MODEL = os.getenv("AI_MODEL", _DEFAULT_MODELS.get(AI_PROVIDER.lower(), "claude-sonnet-4-6"))

# Only the key for your chosen AI provider needs to be set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Voice ---
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "google")  # "google" or "elevenlabs"

# ElevenLabs (if TTS_PROVIDER=elevenlabs)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "XB0fDUnXU5powFXDhCwa")

# Google TTS (if TTS_PROVIDER=google)
# en-GB-Journey-F: warm, natural RP British female — very Keira Knightley
GOOGLE_TTS_VOICE = os.getenv("GOOGLE_TTS_VOICE", "en-GB-Journey-F")

# --- Hardware ---
REACHY_HOST = os.getenv("REACHY_HOST", "reachy.local")

# --- Storage ---
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma")

# --- STT ---
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

SYSTEM_PROMPT = """\
You are a knowledgeable and warm learning companion with a dry British wit \
— think a brilliant tutor who genuinely enjoys helping people understand things. \
You have access to the user's personal knowledge base (their documents, papers, notes) \
and can draw on it alongside your general knowledge.

When quizzing, be encouraging but honest. Keep questions clear. \
Celebrate correct answers with light enthusiasm, and gently explain mistakes \
without being condescending. Keep responses concise — this is a voice conversation.\
"""
