"""Claude API client with prompt caching and RAG context injection."""

import anthropic
from knowledge import store
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Conversation history per session (role/content pairs)
_history: list[dict] = []


def reset_conversation() -> None:
    _history.clear()


def chat(user_message: str, use_knowledge: bool = True) -> str:
    """
    Send a message, optionally enriching with RAG context.
    Uses prompt caching on the system prompt for cost efficiency.
    """
    rag_context = ""
    if use_knowledge and store.count() > 0:
        relevant = store.query(user_message, n_results=4)
        if relevant:
            rag_context = "\n\n<knowledge_base>\n" + "\n---\n".join(relevant) + "\n</knowledge_base>"

    _history.append({"role": "user", "content": user_message})

    system = [
        {
            "type": "text",
            "text": config.SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},  # cache the stable system prompt
        }
    ]
    if rag_context:
        system.append({"type": "text", "text": rag_context})

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=system,
        messages=_history,
    )

    reply = response.content[0].text
    _history.append({"role": "assistant", "content": reply})
    return reply
