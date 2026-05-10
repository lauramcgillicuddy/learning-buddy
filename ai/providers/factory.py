"""Build the configured AI provider from environment settings."""

from .base import AIProvider


def get_provider() -> AIProvider:
    import config

    match config.AI_PROVIDER.lower():
        case "anthropic" | "claude":
            from .anthropic_provider import AnthropicProvider
            return AnthropicProvider(api_key=config.ANTHROPIC_API_KEY, model=config.AI_MODEL)
        case "openai" | "gpt":
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(api_key=config.OPENAI_API_KEY, model=config.AI_MODEL)
        case "gemini" | "google":
            from .gemini_provider import GeminiProvider
            return GeminiProvider(api_key=config.GEMINI_API_KEY, model=config.AI_MODEL)
        case other:
            raise ValueError(
                f"Unknown AI_PROVIDER '{other}'. "
                "Supported values: anthropic, openai, gemini"
            )
