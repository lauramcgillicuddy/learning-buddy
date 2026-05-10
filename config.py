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
}
AI_MODEL = os.getenv("AI_MODEL", _DEFAULT_MODELS.get(AI_PROVIDER.lower(), "claude-sonnet-4-6"))

# --- Voice ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "XB0fDUnXU5powFXDhCwa")

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
