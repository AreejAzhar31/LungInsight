"""
Embedding layer.

Wraps `sentence-transformers` (model: all-MiniLM-L6-v2, 384-dim) behind a
small, swappable interface (`EmbedderProtocol`) so:

  - Production code depends only on `.encode(texts) -> np.ndarray`.
  - Tests can inject a deterministic fake embedder (see tests/conftest.py)
    without downloading model weights or needing network access.

The real model is loaded lazily (on first `.encode()` call) so importing this
module never triggers a network call or slow model load.
"""
from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np


class EmbedderProtocol(Protocol):
    dim: int

    def encode(self, texts: Sequence[str]) -> np.ndarray: ...


class Embedder:
    """Sentence-Transformers embedder (all-MiniLM-L6-v2 by default)."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._model = None  # lazy-loaded

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - exercised only w/o dep installed
                raise ImportError(
                    "sentence-transformers is required for the Embedder. "
                    "Install with: pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Return an (n, dim) float32, L2-normalized embedding matrix."""
        if not texts:
            return np.zeros((0, self.dim), dtype="float32")
        model = self._load()
        vectors = model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine similarity == dot product
            show_progress_bar=False,
        )
        return vectors.astype("float32")
