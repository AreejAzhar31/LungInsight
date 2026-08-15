"""Pydantic schemas for chat endpoints."""

from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prediction_id: uuid.UUID | None
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatSessionStartRequest(BaseModel):
    prediction_id: uuid.UUID | None = Field(
        default=None,
        description="If set, seeds the RAG session with this prediction's label/confidence "
        "so the chatbot's first answers are grounded in the actual result.",
    )


class ChatTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    prediction_id: uuid.UUID | None = Field(
        default=None,
        description="Include on the first turn of a session to ground answers in this "
        "prediction's result. The RAG service remembers it for later turns automatically.",
    )


class RetrievedChunk(BaseModel):
    source: str | None = None
    text: str | None = None
    score: float | None = None

    model_config = ConfigDict(extra="allow")


class ChatTurnResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    citations: list[RetrievedChunk] = Field(default_factory=list)
    is_safe: bool = True
    safety_reason: str | None = None
    verification_passed: bool | None = None
