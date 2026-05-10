"""Quiz mode — generates and evaluates questions from the knowledge base."""

import json
import re
import anthropic
from knowledge import store
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def generate_questions(topic: str | None = None, count: int = 5) -> list[dict]:
    """
    Pull relevant chunks and ask Claude to generate quiz questions.
    Returns list of {question, answer, hint} dicts.
    """
    query = topic or "key concepts and important ideas"
    chunks = store.query(query, n_results=6)
    if not chunks:
        raise ValueError("No documents in knowledge base. Add some first with `buddy add`.")

    context = "\n---\n".join(chunks)
    prompt = f"""\
Based on the following material, generate {count} quiz questions.
Return ONLY a JSON array with objects having keys: "question", "answer", "hint".
Keep questions specific and testable. Vary difficulty.

Material:
{context}"""

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system=[{"type": "text", "text": config.SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    # Extract JSON even if Claude wraps it in markdown code fences
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError("Could not parse questions from Claude's response.")
    return json.loads(match.group())


def evaluate_answer(question: str, correct_answer: str, user_answer: str) -> dict:
    """
    Ask Claude to evaluate a free-text answer.
    Returns {correct: bool, feedback: str, score: int (0-10)}.
    """
    prompt = f"""\
Question: {question}
Correct answer: {correct_answer}
Student's answer: {user_answer}

Evaluate whether the student's answer captures the key ideas of the correct answer.
Return JSON with keys: "correct" (bool), "score" (0-10), "feedback" (1-2 sentences, encouraging tone).
Return ONLY the JSON object."""

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"correct": False, "score": 0, "feedback": "Could not evaluate — try again."}
    return json.loads(match.group())
