"""Pydantic schema for the health check endpoint."""

from __future__ import annotations
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    database: str
    inference_service: str
    rag_service: str
