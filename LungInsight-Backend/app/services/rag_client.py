"""
RAG client — the integration point with the (separately-built) RAG/chatbot
module.

Same pattern as `inference_client.py`: `RagClient` defines the contract,
`StubRagClient` is a placeholder so the backend is fully testable on its
own, and `HttpRagClient` calls the real microservice (rag/api.py) over
HTTP — keeping modules independently deployable, no in-process import of
sentence-transformers/FAISS/LangGraph into this backend.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.exceptions import RagServiceError

logger = logging.getLogger("app.rag_client")


@dataclass
class RagTurnResult:
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    is_safe: bool = True
    safety_reason: str | None = None
    verification_passed: bool | None = None


class RagClient(ABC):
    @abstractmethod
    def chat(
        self,
        session_id: str,
        message: str,
        prediction_context: dict[str, Any] | None = None,
    ) -> RagTurnResult:
        raise NotImplementedError

    @abstractmethod
    def reset(self, session_id: str) -> None:
        raise NotImplementedError


class StubRagClient(RagClient):
    """Deterministic placeholder used by the test suite and whenever
    RAG_MODE=stub, regardless of whether the RAG service is up."""

    def chat(self, session_id: str, message: str, prediction_context: dict[str, Any] | None = None) -> RagTurnResult:
        return RagTurnResult(
            answer="This is a stub response. Connect the RAG service (RAG_MODE=http) for real, "
            "retrieval-grounded clinical answers.",
            citations=[],
            is_safe=True,
            verification_passed=True,
        )

    def reset(self, session_id: str) -> None:
        return None


class HttpRagClient(RagClient):
    """Real client — calls the Module 4 RAG microservice (rag/api.py)."""

    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def chat(self, session_id: str, message: str, prediction_context: dict[str, Any] | None = None) -> RagTurnResult:
        payload: dict[str, Any] = {"session_id": session_id, "message": message}
        if prediction_context is not None:
            payload["prediction_context"] = prediction_context

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise RagServiceError("The clinical assistant timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            raise RagServiceError(f"RAG service returned an error: {detail}") from exc
        except httpx.ConnectError as exc:
            raise RagServiceError(
                f"Could not reach the RAG service. Make sure it is running at {self.base_url}."
            ) from exc

        answer_block = data.get("answer") or {}
        safety = data.get("safety") or {}
        return RagTurnResult(
            answer=answer_block.get("plain_language_explanation") or answer_block.get("raw_text") or "",
            citations=data.get("retrieved_chunks") or [],
            is_safe=safety.get("is_safe", True),
            safety_reason=safety.get("reason"),
            verification_passed=data.get("verification_passed"),
        )

    def reset(self, session_id: str) -> None:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                client.post(f"{self.base_url}/sessions/{session_id}/reset")
        except httpx.HTTPError as exc:
            # Non-fatal — worst case the next chat() call carries stale
            # session memory server-side until it naturally rolls off.
            logger.warning("Failed to reset RAG session %s: %s", session_id, exc)
