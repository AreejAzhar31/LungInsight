"""
LungInsight RAG — Chat Microservice.

Wraps `service.LungInsightRAGService` (Module 4) behind a small HTTP API so
the Backend (Module 2) can call it without an in-process import of
sentence-transformers/FAISS/LangGraph — same "independently deployable
microservice" pattern already used for the AI model in ai/service/main.py.

Run with:
    uvicorn api:app --host 0.0.0.0 --port 8600

Requires GROQ_API_KEY in .env (same file config.py already loads via
load_dotenv). The index is built eagerly at startup (see startup_event
below) and cached in storage/vector_index/ afterwards -- the very first
build (downloading the embedding model, indexing the knowledge base) can
take over a minute, which is fine to absorb once at startup but is NOT
fine to make a real user's first chat message wait through, so it does
not happen lazily on first request anymore.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("lunginsight.rag_service")

app = FastAPI(
    title="LungInsight AI — RAG Chat Service",
    description="Internal microservice: retrieval-grounded clinical Q&A. Not exposed publicly.",
    version="1.0.0",
)

_service = None
_load_error: str | None = None


@app.on_event("startup")
def warm_up_on_startup():
    """Builds the index once, at process startup, instead of on the first
    real chat request. A slow startup is fine -- start-lunginsight.ps1
    already tells the user to wait 10-20s before using the app. A slow
    *first message* is not fine -- it previously caused the backend's
    30s timeout to fire and return 503 before the RAG service even
    finished its one-time model download + index build."""
    try:
        _get_service()
        logger.info("RAG service warm-up complete -- ready for requests.")
    except Exception as exc:  # noqa: BLE001 -- don't crash the process; /health reports it
        logger.error("RAG service warm-up failed, will retry lazily on first request: %s", exc)


def _get_service():
    """Builds the RAG service (and its vector index) once. Normally this
    only actually runs from warm_up_on_startup() above; kept safe to call
    again (e.g. from /chat) in case startup warm-up failed and the
    condition that caused it has since been fixed."""
    global _service, _load_error
    if _service is not None:
        return _service
    try:
        from service import LungInsightRAGService

        svc = LungInsightRAGService()
        svc.ensure_index_built()
        _service = svc
        _load_error = None
    except Exception as exc:  # noqa: BLE001 — surfaced via /health and 503s
        _load_error = str(exc)
        logger.error("RAG service failed to initialize: %s", exc)
        raise
    return _service


class PredictionContext(BaseModel):
    predicted_class: str
    confidence: float
    gradcam_region: str | None = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    prediction_context: PredictionContext | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: dict[str, Any]
    retrieved_chunks: list[dict[str, Any]]
    safety: dict[str, Any]
    verification_passed: bool | None = None


@app.get("/health")
def health():
    try:
        svc = _get_service()
        return {
            "status": "ok",
            "index_loaded": svc.vector_store is not None,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "index_loaded": False, "error": str(exc)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        svc = _get_service()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"RAG service unavailable: {exc}") from exc

    try:
        result = svc.chat(
            session_id=req.session_id,
            message=req.message,
            prediction_context=req.prediction_context.model_dump() if req.prediction_context else None,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat turn failed")
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {exc}") from exc

    return result


@app.post("/sessions/{session_id}/reset")
def reset_session(session_id: str):
    svc = _get_service()
    svc.reset_session(session_id)
    return {"session_id": session_id, "status": "reset"}
