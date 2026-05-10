"""ChromaDB-backed vector store for the knowledge base."""

import hashlib
import chromadb

import config


_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        # Use chromadb's built-in default embedding (ONNX all-MiniLM-L6-v2)
        # rather than wiring in sentence-transformers manually — avoids
        # chromadb 1.x / Python 3.13 type annotation conflicts
        _collection = _client.get_or_create_collection(
            name="knowledge",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_document(chunks: list[str], source: str, tags: list[str] | None = None) -> int:
    """Add chunks to the store. Returns number of chunks added."""
    col = _get_collection()
    ids = [hashlib.sha256(f"{source}:{i}:{c}".encode()).hexdigest()[:16] for i, c in enumerate(chunks)]
    metadatas = [{"source": source, "tags": ",".join(tags or [])} for _ in chunks]
    col.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def query(text: str, n_results: int = 5, tag_filter: str | None = None) -> list[str]:
    """Return the top-n most relevant chunks for the query."""
    col = _get_collection()
    where = {"tags": {"$contains": tag_filter}} if tag_filter else None
    results = col.query(
        query_texts=[text],
        n_results=min(n_results, col.count() or 1),
        where=where,
    )
    return results["documents"][0] if results["documents"] else []


def list_sources() -> list[dict]:
    """List all distinct sources in the store."""
    col = _get_collection()
    if col.count() == 0:
        return []
    results = col.get(include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        src = meta["source"]
        if src not in seen:
            seen[src] = meta
    return list(seen.values())


def delete_source(source: str) -> int:
    """Remove all chunks from a given source. Returns count removed."""
    col = _get_collection()
    results = col.get(where={"source": source}, include=["metadatas"])
    if not results["ids"]:
        return 0
    col.delete(ids=results["ids"])
    return len(results["ids"])


def count() -> int:
    return _get_collection().count()
