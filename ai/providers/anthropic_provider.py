"""Anthropic (Claude) provider with prompt caching."""

import anthropic
from .base import AIProvider


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return f"Anthropic ({self._model})"

    def chat(self, user_message: str, history: list[dict], system: str, context: str = "") -> str:
        system_blocks = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}},
        ]
        if context:
            system_blocks.append({"type": "text", "text": context})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_blocks,
            messages=history + [{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
