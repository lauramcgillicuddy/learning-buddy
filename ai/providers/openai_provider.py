"""OpenAI (GPT) provider."""

import openai
from .base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"OpenAI ({self._model})"

    def chat(self, user_message: str, history: list[dict], system: str, context: str = "") -> str:
        full_system = system + ("\n\n" + context if context else "")
        messages = [{"role": "system", "content": full_system}] + history + [{"role": "user", "content": user_message}]
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=1024,
            messages=messages,
        )
        return response.choices[0].message.content

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
