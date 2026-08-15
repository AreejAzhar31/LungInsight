"""
Ingestion pipeline orchestrator.

    Documents -> Chunking -> Embeddings -> Vector Database

Run standalone:
    python -m ingestion.ingest_pipeline

This (re)builds the vector index from knowledge_base/raw/ and persists it to
storage/vector_index/, so the conversational agent can load a pre-built index
at request time instead of re-embedding documents on every startup.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from ingestion.chunker import chunk_documents
from ingestion.embedder import Embedder, EmbedderProtocol
from ingestion.loader import load_documents
from ingestion.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingest_pipeline")


def build_index(
    source_dir: Path | None = None,
    embedder: EmbedderProtocol | None = None,
    persist_dir: Path | None = None,
) -> VectorStore:
    source_dir = source_dir or settings.knowledge_base_dir
    persist_dir = persist_dir or settings.vector_store_dir
    embedder = embedder or Embedder(settings.embedding_model_name, dim=settings.embedding_dim)

    logger.info("Loading documents from %s", source_dir)
    documents = load_documents(source_dir)
    logger.info("Loaded %d documents", len(documents))

    chunks = chunk_documents(
        documents,
        chunk_size_tokens=settings.chunk_size_tokens,
        chunk_overlap_tokens=settings.chunk_overlap_tokens,
    )
    logger.info("Produced %d chunks (size=%d, overlap=%d tokens)", len(chunks), settings.chunk_size_tokens, settings.chunk_overlap_tokens)

    texts = [c.text for c in chunks]
    embeddings = embedder.encode(texts)
    logger.info("Embedded %d chunks -> shape=%s", len(chunks), embeddings.shape)

    store = VectorStore(dim=embedder.dim, backend=settings.vector_store_backend)
    store.add(chunks, embeddings)
    logger.info("Vector store backend in use: %s", store.backend_name)

    store.persist(persist_dir)
    logger.info("Persisted index to %s", persist_dir)

    return store


if __name__ == "__main__":
    build_index()
