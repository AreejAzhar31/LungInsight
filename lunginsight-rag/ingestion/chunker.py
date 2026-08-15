"""
Chunking strategy.

We use a heading-aware, sliding-window chunker:

1. Split the document on Markdown headings (`#`, `##`, ...) so that a chunk
   never silently blends two unrelated sections (e.g. "Risk Factors" text
   bleeding into "Treatment" text).
2. Within each section, apply a token-approximate sliding window with overlap
   so that no chunk exceeds `chunk_size_tokens` and adjacent chunks retain
   `chunk_overlap_tokens` of shared context (this reduces the chance that a
   fact gets split exactly at a chunk boundary and becomes unretrievable).
3. Every chunk keeps a back-reference to its parent document's metadata, plus
   the heading path it came from, so citations can be as specific as
   "WHO — Lung Cancer Overview — Screening Context".

Token counting here is approximate (whitespace tokenization) to avoid a hard
dependency on a specific tokenizer; this is intentionally conservative
(slightly over-counts) which keeps chunks safely under embedding model limits.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .loader import Document

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    organization: str
    topic: str
    source_url: str
    retrieved_date: str
    section_heading: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (heading, section_body) using Markdown headings."""
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _sliding_window(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if len(words) <= size:
        return [words]
    step = max(size - overlap, 1)
    windows = []
    i = 0
    while i < len(words):
        window = words[i : i + size]
        if window:
            windows.append(window)
        if i + size >= len(words):
            break
        i += step
    return windows


def chunk_document(
    document: Document,
    chunk_size_tokens: int = 220,
    chunk_overlap_tokens: int = 40,
) -> list[Chunk]:
    """Chunk a single Document into heading-scoped, size-bounded Chunks."""
    sections = _split_into_sections(document.text)
    chunks: list[Chunk] = []
    chunk_index = 0

    for heading, body in sections:
        words = body.split()
        for window in _sliding_window(words, chunk_size_tokens, chunk_overlap_tokens):
            chunk_text = " ".join(window)
            # Prefix section heading into the embedded text for better retrieval
            # of section-specific queries (e.g. "screening" -> Screening section).
            embedding_text = f"{document.title} — {heading}\n{chunk_text}" if heading else chunk_text
            chunk_id = f"{document.document_id}::chunk-{chunk_index}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    title=document.title,
                    organization=document.organization,
                    topic=document.topic,
                    source_url=document.source_url,
                    retrieved_date=document.retrieved_date,
                    section_heading=heading,
                    text=embedding_text,
                    metadata={"raw_text": chunk_text, "word_count": len(window)},
                )
            )
            chunk_index += 1

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size_tokens: int = 220,
    chunk_overlap_tokens: int = 40,
) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(
            chunk_document(doc, chunk_size_tokens=chunk_size_tokens, chunk_overlap_tokens=chunk_overlap_tokens)
        )
    return all_chunks
