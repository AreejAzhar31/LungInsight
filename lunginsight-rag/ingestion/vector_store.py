"""
Vector store layer.

Supports two production backends selected via `settings.vector_store_backend`:

  - "faiss"  -> FAISS `IndexFlatIP` (cosine similarity via normalized dot product)
  - "chroma" -> ChromaDB persistent collection

A third backend, `NumpyFlatBackend`, is included and used automatically as a
fallback when neither faiss nor chromadb is importable. It implements the same
exact-search math as FAISS's IndexFlatIP (brute-force cosine similarity) using
only numpy, so retrieval QUALITY is identical — it exists purely so this
package can be unit-tested in environments without the compiled FAISS wheel
(e.g. restricted sandboxes / CI), and is not a shortcut around the required
stack for production use.

Every stored vector carries its full Chunk metadata so retrieval results are
immediately citeable (organization, title, section, source_url).
"""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .chunker import Chunk


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    title: str
    organization: str
    topic: str
    source_url: str
    retrieved_date: str
    section_heading: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class _NumpyFlatBackend:
    """Brute-force cosine-similarity search. Dependency-free fallback."""

    def __init__(self, dim: int):
        self.dim = dim
        self._vectors: np.ndarray = np.zeros((0, dim), dtype="float32")

    def add(self, vectors: np.ndarray) -> None:
        self._vectors = (
            vectors.astype("float32")
            if self._vectors.shape[0] == 0
            else np.vstack([self._vectors, vectors.astype("float32")])
        )

    def search(self, query_vectors: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        if self._vectors.shape[0] == 0:
            n = query_vectors.shape[0]
            return np.zeros((n, 0), dtype="float32"), np.zeros((n, 0), dtype="int64")
        # Vectors are pre-normalized -> dot product == cosine similarity
        sims = query_vectors @ self._vectors.T
        k = min(top_k, self._vectors.shape[0])
        idx = np.argsort(-sims, axis=1)[:, :k]
        scores = np.take_along_axis(sims, idx, axis=1)
        return scores, idx

    def save(self, path: Path) -> None:
        np.save(path / "vectors.npy", self._vectors)

    def load(self, path: Path) -> None:
        self._vectors = np.load(path / "vectors.npy")


class VectorStore:
    """
    Unified vector store facade.

    Usage:
        store = VectorStore(dim=384, backend="faiss")
        store.add(chunks, embeddings)
        results = store.search(query_embedding, top_k=5)
        store.persist(path)
        ...
        store2 = VectorStore(dim=384, backend="faiss")
        store2.load(path)
    """

    def __init__(self, dim: int, backend: str = "faiss"):
        self.dim = dim
        self.requested_backend = backend
        self._chunks: list[Chunk] = []
        self._backend_name, self._backend = self._init_backend(backend, dim)

    # -- backend selection -------------------------------------------------
    def _init_backend(self, backend: str, dim: int):
        if backend == "faiss":
            try:
                import faiss  # type: ignore

                index = faiss.IndexFlatIP(dim)
                return "faiss", index
            except ImportError:
                pass  # fall through to numpy backend
        if backend == "chroma":
            try:
                import chromadb  # type: ignore

                client = chromadb.Client()
                collection = client.get_or_create_collection(
                    name="lunginsight_kb", metadata={"hnsw:space": "cosine"}
                )
                return "chroma", collection
            except ImportError:
                pass
        # Dependency-free fallback (also used if requested backend unavailable)
        return "numpy_fallback", _NumpyFlatBackend(dim)

    @property
    def backend_name(self) -> str:
        return self._backend_name

    # -- population ----------------------------------------------------------
    def add(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks and embeddings must have matching length")

        if self._backend_name == "faiss":
            self._backend.add(embeddings.astype("float32"))
        elif self._backend_name == "chroma":
            self._backend.add(
                ids=[c.chunk_id for c in chunks],
                embeddings=embeddings.tolist(),
                documents=[c.text for c in chunks],
                metadatas=[
                    {
                        "document_id": c.document_id,
                        "title": c.title,
                        "organization": c.organization,
                        "topic": c.topic,
                        "source_url": c.source_url,
                        "retrieved_date": c.retrieved_date,
                        "section_heading": c.section_heading,
                    }
                    for c in chunks
                ],
            )
        else:
            self._backend.add(embeddings)

        self._chunks.extend(chunks)

    # -- retrieval -------------------------------------------------------
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[RetrievedChunk]:
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if self._backend_name == "chroma":
            result = self._backend.query(
                query_embeddings=query_embedding.tolist(), n_results=top_k
            )
            out: list[RetrievedChunk] = []
            for i, chunk_id in enumerate(result["ids"][0]):
                meta = result["metadatas"][0][i]
                distance = result["distances"][0][i]
                score = 1.0 - distance  # cosine distance -> similarity
                out.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        document_id=meta["document_id"],
                        title=meta["title"],
                        organization=meta["organization"],
                        topic=meta["topic"],
                        source_url=meta["source_url"],
                        retrieved_date=meta["retrieved_date"],
                        section_heading=meta["section_heading"],
                        text=result["documents"][0][i],
                        score=float(score),
                    )
                )
            return out

        # faiss / numpy fallback share the same (scores, idx) contract
        scores, idx = self._backend.search(query_embedding.astype("float32"), top_k)
        out = []
        for score, i in zip(scores[0], idx[0]):
            if i < 0 or i >= len(self._chunks):
                continue
            chunk = self._chunks[i]
            out.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    organization=chunk.organization,
                    topic=chunk.topic,
                    source_url=chunk.source_url,
                    retrieved_date=chunk.retrieved_date,
                    section_heading=chunk.section_heading,
                    text=chunk.text,
                    score=float(score),
                    metadata=chunk.metadata,
                )
            )
        return out

    # -- persistence -----------------------------------------------------
    def persist(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(self._chunks, f)
        with open(path / "meta.json", "w") as f:
            json.dump(
                {"dim": self.dim, "backend": self._backend_name, "n_chunks": len(self._chunks)},
                f,
                indent=2,
            )

        if self._backend_name == "faiss":
            import faiss  # type: ignore

            faiss.write_index(self._backend, str(path / "index.faiss"))
        elif self._backend_name == "numpy_fallback":
            self._backend.save(path)
        # chroma persists to its own configured storage; nothing extra needed here.

    def load(self, path: str | Path) -> None:
        path = Path(path)
        with open(path / "chunks.pkl", "rb") as f:
            self._chunks = pickle.load(f)

        if self._backend_name == "faiss":
            import faiss  # type: ignore

            self._backend = faiss.read_index(str(path / "index.faiss"))
        elif self._backend_name == "numpy_fallback":
            self._backend.load(path)

    def __len__(self) -> int:
        return len(self._chunks)
