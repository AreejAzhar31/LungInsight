"""
LungInsightRAGService — the single entry point this standalone service
exposes to whatever wraps it later (a REST API, a message queue consumer,
the CLI in `cli.py`, etc.).

This module intentionally has NO web framework, NO auth, NO CNN/GradCAM code.
It assumes prediction data (e.g. `{"predicted_class": "malignant_nodule",
"confidence": 0.82, "gradcam_region": "right upper lobe"}`) will be handed to
it by an upstream API layer — see `chat(..., prediction_context=...)`.

Typical usage:

    from service import LungInsightRAGService

    rag = LungInsightRAGService()
    rag.ensure_index_built()  # builds once, reuses on subsequent calls

    result = rag.chat(
        session_id="user-123",
        message="What does this finding mean?",
        prediction_context={
            "predicted_class": "suspicious_nodule",
            "confidence": 0.78,
            "gradcam_region": "right upper lobe",
        },
    )
    print(result["answer"]["plain_language_explanation"])
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from config import settings
from agent.graph import build_graph
from agent.llm_client import GroqLLMClient, LLMClientProtocol
from agent.memory import ConversationMemory
from ingestion.embedder import Embedder, EmbedderProtocol
from ingestion.ingest_pipeline import build_index
from ingestion.vector_store import VectorStore


class LungInsightRAGService:
    def __init__(
        self,
        embedder: EmbedderProtocol | None = None,
        llm_client: LLMClientProtocol | None = None,
        vector_store: VectorStore | None = None,
        memory: ConversationMemory | None = None,
    ):
        self.embedder = embedder or Embedder(settings.embedding_model_name, dim=settings.embedding_dim)
        self.llm_client = llm_client or GroqLLMClient(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_s=settings.llm_timeout_s,
        )
        self.memory = memory or ConversationMemory(max_turns=settings.max_turns_in_memory)
        self.vector_store = vector_store
        self._graph = None

    # -- index lifecycle ---------------------------------------------------
    def ensure_index_built(self, force_rebuild: bool = False) -> None:
        """Build the vector index from knowledge_base/raw/ if not already loaded/persisted."""
        if self.vector_store is not None and not force_rebuild:
            return

        index_dir = settings.vector_store_dir
        if not force_rebuild and (index_dir / "meta.json").exists():
            store = VectorStore(dim=self.embedder.dim, backend=settings.vector_store_backend)
            store.load(index_dir)
            self.vector_store = store
        else:
            self.vector_store = build_index(embedder=self.embedder)

        self._graph = None  # force rebuild of graph with the new store

    def _get_graph(self):
        if self._graph is None:
            if self.vector_store is None:
                self.ensure_index_built()
            self._graph = build_graph(self.embedder, self.vector_store, self.llm_client, self.memory)
        return self._graph

    # -- conversational entry point ----------------------------------------
    def chat(
        self,
        session_id: str,
        message: str,
        prediction_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run one conversational turn. Retrieval, safety checks, generation,
        and verification all happen inside the graph; this method only wires
        session memory in/out.
        """
        graph = self._get_graph()

        if prediction_context is not None:
            self.memory.set_prediction_context(session_id, prediction_context)
        else:
            prediction_context = self.memory.get_prediction_context(session_id)

        history = self.memory.get_history(session_id)

        initial_state = {
            "user_message": message,
            "prediction_context": prediction_context,
            "history": history,
            "regeneration_attempts": 0,
        }

        final_state = graph.invoke(initial_state)

        # Persist the turn regardless of refusal, so repeated unsafe/empty
        # queries don't silently vanish from the transcript a clinician might
        # audit later.
        self.memory.add_turn(session_id, "user", message)
        answer = final_state.get("answer") or {}
        self.memory.add_turn(session_id, "assistant", answer.get("raw_text", ""))

        return {
            "session_id": session_id,
            "answer": answer,
            "retrieved_chunks": final_state.get("retrieved_chunks", []),
            "safety": {
                "is_safe": final_state.get("is_safe", True),
                "reason": final_state.get("safety_reason"),
            },
            "verification_passed": final_state.get("verification_passed"),
        }

    def reset_session(self, session_id: str) -> None:
        self.memory.clear(session_id)
