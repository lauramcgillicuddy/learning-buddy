"""Google Gemini provider."""

import google.generativeai as genai
from .base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self._model_name = model
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        return f"Google Gemini ({self._model_name})"

    def chat(self, user_message: str, history: list[dict], system: str, context: str = "") -> str:
        full_system = system + ("\n\n" + context if context else "")
        model = genai.GenerativeModel(self._model_name, system_instruction=full_system)

        # Convert history to Gemini format (role: user/model)
        gemini_history = []
        for msg in history:
            gemini_history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            })

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)
        return response.text

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self._model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
        )
        return response.text
