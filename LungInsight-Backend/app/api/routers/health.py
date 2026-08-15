"""Health check endpoint — no auth required, used by uptime monitors/load balancers."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.schemas.health import HealthResponse

settings = get_settings()
router = APIRouter(tags=["Health"])


def _probe(url: str, mode: str) -> str:
    """Best-effort check of a dependency microservice's /health endpoint.
    Never raises — a dependency being down must not break this endpoint."""
    if mode != "http":
        return "stub"
    try:
        resp = httpx.get(f"{url.rstrip('/')}/health", timeout=2.0)
        resp.raise_for_status()
        return "connected" if resp.json().get("status") == "ok" else "degraded"
    except Exception:
        return "unavailable"


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unavailable"

    inference_status = _probe(settings.inference_service_url, settings.inference_mode)
    rag_status = _probe(settings.rag_service_url, settings.rag_mode)

    overall = "ok" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall,
        app_name=settings.app_name,
        database=db_status,
        inference_service=inference_status,
        rag_service=rag_status,
    )
