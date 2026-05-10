"""Stateful chat client — provider-agnostic."""

from knowledge import store
from ai.providers.factory import get_provider
import config

_provider = None
_history: list[dict] = []


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider


def reset_conversation() -> None:
    _history.clear()


def chat(user_message: str, use_knowledge: bool = True) -> str:
    provider = _get_provider()

    rag_context = ""
    if use_knowledge and store.count() > 0:
        relevant = store.query(user_message, n_results=4)
        if relevant:
            rag_context = "<knowledge_base>\n" + "\n---\n".join(relevant) + "\n</knowledge_base>"

    reply = provider.chat(
        user_message=user_message,
        history=_history,
        system=config.SYSTEM_PROMPT,
        context=rag_context,
    )

    _history.append({"role": "user", "content": user_message})
    _history.append({"role": "assistant", "content": reply})
    return reply


def provider_name() -> str:
    return _get_provider().name
