"""Pydantic schemas for feedback endpoints."""

from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    prediction_id: uuid.UUID
    rating: int = Field(ge=1, le=5, description="1 (strongly disagree) to 5 (strongly agree)")
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prediction_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime
