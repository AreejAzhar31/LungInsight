"""
Central configuration for the LungInsight AI RAG service.

All values can be overridden via environment variables so the service can be
deployed without code changes. Nothing here reaches out to the network at
import time.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # --- Paths -------------------------------------------------------
    knowledge_base_dir: Path = PROJECT_ROOT / "knowledge_base" / "raw"
    sources_manifest: Path = PROJECT_ROOT / "knowledge_base" / "sources.json"
    vector_store_dir: Path = PROJECT_ROOT / "storage" / "vector_index"

    # --- Embeddings ----------------------------------------------------
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )
    embedding_dim: int = 384  # all-MiniLM-L6-v2 output dimension

    # --- Chunking --------------------------------------------------------
    chunk_size_tokens: int = int(os.getenv("CHUNK_SIZE_TOKENS", "220"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "40"))

    # --- Vector store ------------------------------------------------
    vector_store_backend: str = os.getenv("VECTOR_STORE_BACKEND", "faiss")  # "faiss" | "chroma"
    top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    similarity_score_floor: float = float(os.getenv("SIMILARITY_SCORE_FLOOR", "0.35"))
    min_supporting_chunks: int = int(os.getenv("MIN_SUPPORTING_CHUNKS", "1"))

    # --- LLM (Groq) ----------------------------------------------------
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "900"))
    llm_timeout_s: int = int(os.getenv("LLM_TIMEOUT_S", "30"))

    # --- Conversation memory --------------------------------------------
    max_turns_in_memory: int = int(os.getenv("MAX_TURNS_IN_MEMORY", "8"))

    # --- Safety ----------------------------------------------------------
    max_user_message_chars: int = int(os.getenv("MAX_USER_MESSAGE_CHARS", "4000"))
    require_citations: bool = os.getenv("REQUIRE_CITATIONS", "true").lower() == "true"


settings = Settings()