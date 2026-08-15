"""
Document loader.

Reads the trusted-source markdown files under knowledge_base/raw/, parses the
simple frontmatter block (title/organization/topic/source_url/etc.), and
returns clean Document objects ready for chunking.

Design notes:
- We keep the frontmatter parser dependency-free (no PyYAML requirement) since
  the frontmatter here is a flat key: value block.
- Metadata is preserved end-to-end (document -> chunk -> vector store) so every
  answer can cite an organization + URL, not just a filename.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass
class Document:
    document_id: str
    title: str
    organization: str
    topic: str
    source_url: str
    retrieved_date: str
    text: str
    file_path: str
    extra: dict[str, Any] = field(default_factory=dict)


def _parse_frontmatter(raw_text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(raw_text)
    if not match:
        return {}, raw_text.strip()

    frontmatter_block, body = match.groups()
    meta: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def load_documents(source_dir: Path) -> list[Document]:
    """Load every .md file in `source_dir` into a Document."""
    documents: list[Document] = []
    if not source_dir.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {source_dir}")

    for file_path in sorted(source_dir.glob("*.md")):
        raw = file_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)

        document_id = meta.get("document_id") or file_path.stem
        documents.append(
            Document(
                document_id=document_id,
                title=meta.get("title", file_path.stem),
                organization=meta.get("organization", "Unknown"),
                topic=meta.get("topic", "general"),
                source_url=meta.get("source_url", ""),
                retrieved_date=meta.get("retrieved_date", ""),
                text=body,
                file_path=str(file_path),
                extra={k: v for k, v in meta.items() if k not in {
                    "document_id", "title", "organization", "topic",
                    "source_url", "retrieved_date",
                }},
            )
        )

    if not documents:
        raise ValueError(f"No documents found in {source_dir}")

    return documents
