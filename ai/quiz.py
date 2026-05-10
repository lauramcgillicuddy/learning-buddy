"""Quiz mode — generates and evaluates questions at three difficulty levels."""

import json
import re
from knowledge import store
from ai.providers.factory import get_provider
import config

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider


# ── Difficulty profiles ───────────────────────────────────────────────────────

_DIFFICULTY_PROFILES = {
    "friendly": {
        "label": "Friendly",
        "question_instruction": (
            "Generate {count} beginner-friendly quiz questions. "
            "Focus on key definitions and core concepts. "
            "Include a helpful hint for each question. "
            "Questions should build confidence."
        ),
        "eval_instruction": (
            "Be warm and encouraging. Award generous partial credit for answers that show "
            "understanding even if imprecise. Feedback should celebrate what they got right "
            "before gently noting gaps. Max 2 sentences."
        ),
    },
    "standard": {
        "label": "Standard",
        "question_instruction": (
            "Generate {count} quiz questions that vary in difficulty — mix recall, "
            "comprehension, and some application questions. Include a brief hint for each."
        ),
        "eval_instruction": (
            "Be balanced and honest. Award credit for correct reasoning even if wording differs. "
            "Point out gaps clearly but kindly. Max 2 sentences."
        ),
    },
    "viva": {
        "label": "MSc Viva",
        "question_instruction": (
            "Generate {count} rigorous examination-level questions as a dissertation supervisor "
            "would ask in a viva. Prioritise analysis, evaluation, and synthesis over recall. "
            "Ask 'why', 'what are the limitations of', 'how does this compare to', "
            "'what would happen if'. Do NOT include hints — this is an exam. "
            "At least one question should probe a potential weakness or controversy in the material."
        ),
        "eval_instruction": (
            "You are a rigorous but fair examiner. Do not soften criticism. "
            "If the answer is vague, incomplete, or shows a misconception, say so directly. "
            "Award marks only for accurate, substantive content. "
            "If the answer is strong, acknowledge it briefly and note what could be deeper. "
            "Max 3 sentences. Do not use encouraging filler phrases."
        ),
    },
}

# Follow-up questions for viva mode — pushed after each answer
_VIVA_FOLLOWUPS = [
    "Can you elaborate on the mechanism behind that?",
    "What are the limitations of that approach?",
    "How does this relate to the broader field?",
    "What evidence supports that claim?",
    "What would a critic of this view argue?",
]


def get_difficulty_labels() -> list[str]:
    return [p["label"] for p in _DIFFICULTY_PROFILES.values()]


def difficulty_from_label(label: str) -> str:
    for key, profile in _DIFFICULTY_PROFILES.items():
        if profile["label"].lower() == label.lower():
            return key
    return "standard"


def generate_questions(topic: str | None = None, count: int = 5, difficulty: str | None = None) -> list[dict]:
    difficulty = difficulty or config.QUIZ_DIFFICULTY
    profile = _DIFFICULTY_PROFILES.get(difficulty, _DIFFICULTY_PROFILES["standard"])

    query = topic or "key concepts and important ideas"
    chunks = store.query(query, n_results=6)
    if not chunks:
        raise ValueError("No documents in knowledge base. Add some first with 📚 Knowledge Base.")

    context = "\n---\n".join(chunks)
    instruction = profile["question_instruction"].format(count=count)
    prompt = f"""\
{instruction}

Return ONLY a JSON array. Each object must have:
  "question": the question text
  "answer": the ideal answer
  "hint": a helpful hint (use empty string "" if difficulty is viva)

Material:
{context}"""

    raw = _get_provider().complete(prompt)
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError("Could not parse questions from the AI response.")
    return json.loads(match.group())


def evaluate_answer(question: str, correct_answer: str, user_answer: str, difficulty: str | None = None) -> dict:
    """Returns {correct: bool, score: int 0-10, feedback: str, followup: str | None}."""
    difficulty = difficulty or config.QUIZ_DIFFICULTY
    profile = _DIFFICULTY_PROFILES.get(difficulty, _DIFFICULTY_PROFILES["standard"])

    prompt = f"""\
Question: {question}
Correct answer: {correct_answer}
Student's answer: {user_answer}

Evaluation instruction: {profile["eval_instruction"]}

Return ONLY a JSON object with keys:
  "correct": bool
  "score": integer 0-10
  "feedback": string (your evaluation)
  {"'followup': string (one sharp follow-up question to probe deeper, or empty string if answer was weak)" if difficulty == "viva" else '"followup": ""'}
"""

    raw = _get_provider().complete(prompt, max_tokens=300)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"correct": False, "score": 0, "feedback": "Could not evaluate — try again.", "followup": ""}
    result = json.loads(match.group())
    result.setdefault("followup", "")
    return result
