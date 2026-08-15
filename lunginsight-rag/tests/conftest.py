"""
Shared test fixtures.

The real stack (sentence-transformers + Groq) requires network access to
download model weights / call the API. To keep this test suite runnable
offline and deterministically, we provide:

- `FakeEmbedder`: a deterministic hashed bag-of-words embedder. It has no
  semantic understanding, but cosine similarity between its vectors tracks
  lexical word overlap closely enough to validate retrieval *plumbing*
  (chunking -> embedding -> indexing -> search -> ranking) end-to-end against
  the real knowledge base documents. It is NOT a substitute for evaluating
  the real sentence-transformers model's semantic retrieval quality — see
  docs/RAG.md "Testing" section for how to run the real-model eval.
- `FakeLLMClient`: synthesizes a rules-following structured answer (or,
  variants that deliberately break the rules) so `agent/nodes.py` and
  `agent/safety.py` can be tested without calling Groq.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
import pytest

from ingestion.chunker import chunk_documents
from ingestion.loader import load_documents
from ingestion.vector_store import VectorStore

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base" / "raw"


class FakeEmbedder:
    """Deterministic hashed bag-of-words embedder (see module docstring)."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _vector_for(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype="float32")
        words = re.findall(r"[a-z0-9]+", text.lower())
        for w in words:
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            idx = h % self.dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def encode(self, texts):
        if not texts:
            return np.zeros((0, self.dim), dtype="float32")
        return np.stack([self._vector_for(t) for t in texts]).astype("float32")


class FakeLLMClient:
    """
    Produces a rules-following structured answer using only chunk IDs found
    in the prompt's context block, so citation-verification tests exercise
    real parsing logic instead of a hardcoded string.
    """

    def __init__(self, mode: str = "good"):
        self.mode = mode  # "good" | "no_citations" | "fabricated_citation" | "no_disclaimer"
        self.calls: list[tuple[str, str]] = []

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        ids = re.findall(r"ID: ([a-zA-Z0-9_\-]+::chunk-\d+)", user_prompt)

        if not ids:
            return (
                "Plain-language explanation: I don't have enough verified information to answer that.\n"
                "Clinical explanation: \nRecommended next steps: \nSources: \n"
                "Confidence & disclaimer: This is not medical advice. Please consult a clinician."
            )

        cite = f"[cite:{ids[0]}]"

        if self.mode == "no_citations":
            return (
                "Plain-language explanation: Lung cancer risk rises with smoking.\n"
                "Clinical explanation: Tobacco exposure is the dominant risk factor.\n"
                "Recommended next steps: Discuss screening with a clinician.\n"
                "Sources: WHO\n"
                "Confidence & disclaimer: This is not medical advice. Please consult a clinician."
            )

        if self.mode == "fabricated_citation":
            return (
                f"Plain-language explanation: Risk rises with smoking. [cite:fake-doc::chunk-999]\n"
                "Clinical explanation: Tobacco exposure is dominant. [cite:fake-doc::chunk-999]\n"
                "Recommended next steps: Discuss screening with a clinician.\n"
                "Sources: WHO\n"
                "Confidence & disclaimer: This is not medical advice. Please consult a clinician."
            )

        if self.mode == "no_disclaimer":
            return (
                f"Plain-language explanation: Risk rises with smoking. {cite}\n"
                f"Clinical explanation: Tobacco exposure is dominant. {cite}\n"
                "Recommended next steps: Discuss screening with a clinician.\n"
                "Sources: WHO\n"
            )

        # "good" (default): well-formed, cites only real retrieved IDs.
        body_ids = ids[:2] if len(ids) >= 2 else ids
        cites = " ".join(f"[cite:{i}]" for i in body_ids)
        source_lines = "\n".join(f"- {i}" for i in body_ids)
        return (
            f"Plain-language explanation: Based on trusted sources, several factors are linked "
            f"to lung cancer risk and typical next steps. {cites}\n"
            f"Clinical explanation: The retrieved reference material outlines relevant clinical "
            f"context for this question. {cites}\n"
            "Recommended next steps: Discuss findings with a qualified clinician and consider "
            "appropriate follow-up imaging or specialist referral.\n"
            f"Sources:\n{source_lines}\n"
            "Confidence & disclaimer: This explanation is based on retrieved reference material "
            "and is not a medical diagnosis. Please consult a qualified healthcare provider."
        )


@pytest.fixture(scope="session")
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder(dim=384)


@pytest.fixture(scope="session")
def real_documents():
    return load_documents(KB_DIR)


@pytest.fixture(scope="session")
def real_chunks(real_documents):
    return chunk_documents(real_documents, chunk_size_tokens=220, chunk_overlap_tokens=40)


@pytest.fixture(scope="session")
def populated_vector_store(real_chunks, fake_embedder):
    # Requesting an unrecognized backend name deterministically routes to the
    # dependency-free numpy fallback (see VectorStore._init_backend), which is
    # what we want for a reproducible, offline test run.
    store = VectorStore(dim=fake_embedder.dim, backend="numpy_fallback")
    embeddings = fake_embedder.encode([c.text for c in real_chunks])
    store.add(real_chunks, embeddings)
    return store


def make_good_llm_client() -> FakeLLMClient:
    return FakeLLMClient(mode="good")
