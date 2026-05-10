"""Ingest documents from various sources into plain text chunks."""

from pathlib import Path
from typing import Generator


def _chunk(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


def ingest_pdf(path: str | Path) -> list[str]:
    import fitz  # pymupdf
    doc = fitz.open(str(path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return _chunk(text)


def ingest_text(content: str) -> list[str]:
    return _chunk(content)


def ingest_markdown(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    # Strip markdown syntax for cleaner embeddings
    from markdown_it import MarkdownIt
    md = MarkdownIt()
    tokens = md.parse(text)
    plain = []
    for token in tokens:
        if token.children:
            for child in token.children:
                if child.type == "inline" and child.content:
                    plain.append(child.content)
        elif token.content:
            plain.append(token.content)
    return _chunk("\n".join(plain))


def ingest_url(url: str) -> list[str]:
    import trafilatura
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Could not fetch content from: {url}")
    text = trafilatura.extract(downloaded)
    if not text:
        raise ValueError(f"Could not extract readable text from: {url}")
    return _chunk(text)


def ingest(source: str, source_type: str | None = None) -> tuple[list[str], str]:
    """
    Auto-detect or use provided source_type.
    Returns (chunks, resolved_source_type).
    """
    if source_type is None:
        if source.startswith("http://") or source.startswith("https://"):
            source_type = "url"
        elif source.endswith(".pdf"):
            source_type = "pdf"
        elif source.endswith(".md"):
            source_type = "markdown"
        else:
            source_type = "text"

    match source_type:
        case "pdf":
            return ingest_pdf(source), "pdf"
        case "markdown":
            return ingest_markdown(source), "markdown"
        case "url":
            return ingest_url(source), "url"
        case "text":
            return ingest_text(source), "text"
        case _:
            raise ValueError(f"Unknown source type: {source_type}")
