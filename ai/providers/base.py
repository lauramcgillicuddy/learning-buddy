"""Abstract base for all AI providers."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def chat(self, user_message: str, history: list[dict], system: str, context: str = "") -> str:
        """Send a message and return the reply as a string."""
        ...

    @abstractmethod
    def complete(self, prompt: str, max_tokens: int = 2048) -> str:
        """One-shot completion with no history (used for quiz generation/evaluation)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...
