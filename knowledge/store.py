"""Lightweight in-memory knowledge store using TF-IDF — no external DB needed."""

import json
import re
import math
import os
import hashlib
from collections import Counter

# In-memory state
_documents: list[dict] = []   # {id, text, source, tags}
_idf: dict[str, float] = {}
_idf_dirty = True
_loaded = False


# ── Persistence ───────────────────────────────────────────────────────────────

def _store_path() -> str:
    import config
    os.makedirs(config.CHROMA_DB_PATH, exist_ok=True)
    return os.path.join(config.CHROMA_DB_PATH, "store.json")


def _load():
    global _documents, _loaded, _idf_dirty
    if _loaded:
        return
    path = _store_path()
    if os.path.exists(path):
        with open(path) as f:
            _documents = json.load(f)
    _idf_dirty = True
    _loaded = True


def _save():
    with open(_store_path(), "w") as f:
        json.dump(_documents, f)


# ── TF-IDF ────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z]{2,}\b", text.lower())


def _build_idf():
    global _idf, _idf_dirty
    if not _idf_dirty:
        return
    df: Counter = Counter()
    for doc in _documents:
        for term in set(_tokenize(doc["text"])):
            df[term] += 1
    n = len(_documents) or 1
    _idf = {t: math.log((n + 1) / (v + 1)) for t, v in df.items()}
    _idf_dirty = False


def _tfidf(tokens: list[str]) -> dict[str, float]:
    _build_idf()
    tf = Counter(tokens)
    n = len(tokens) or 1
    return {t: (c / n) * _idf.get(t, 0.0) for t, c in tf.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(a.get(t, 0.0) * v for t, v in b.items())
    mag_a = math.sqrt(sum(v * v for v in a.values())) or 1.0
    mag_b = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (mag_a * mag_b)


# ── Public API ────────────────────────────────────────────────────────────────

def add_document(chunks: list[str], source: str, tags: list[str] | None = None) -> int:
    _load()
    global _idf_dirty
    tag_str = ",".join(tags or [])
    for i, text in enumerate(chunks):
        doc_id = hashlib.sha256(f"{source}:{i}:{text}".encode()).hexdigest()[:16]
        # Replace existing chunk with same id
        _documents[:] = [d for d in _documents if d["id"] != doc_id]
        _documents.append({"id": doc_id, "text": text, "source": source, "tags": tag_str})
    _idf_dirty = True
    _save()
    return len(chunks)


def query(text: str, n_results: int = 5, tag_filter: str | None = None) -> list[str]:
    _load()
    if not _documents:
        return []
    q_vec = _tfidf(_tokenize(text))
    if not q_vec:
        return [d["text"] for d in _documents[:n_results]]
    scored = []
    for doc in _documents:
        if tag_filter and tag_filter not in doc.get("tags", ""):
            continue
        d_vec = _tfidf(_tokenize(doc["text"]))
        scored.append((doc["text"], _cosine(q_vec, d_vec)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in scored[:n_results]]


def list_sources() -> list[dict]:
    _load()
    seen: dict[str, dict] = {}
    for doc in _documents:
        src = doc["source"]
        if src not in seen:
            seen[src] = {"source": src, "tags": doc.get("tags", "")}
    return list(seen.values())


def delete_source(source: str) -> int:
    _load()
    global _idf_dirty
    before = len(_documents)
    _documents[:] = [d for d in _documents if d["source"] != source]
    removed = before - len(_documents)
    if removed:
        _idf_dirty = True
        _save()
    return removed


def count() -> int:
    _load()
    return len(_documents)
