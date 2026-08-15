"""Pydantic schemas for prediction endpoints."""

from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_id: uuid.UUID
    label: str
    confidence: float
    heatmap_path: str | None
    created_at: datetime


class PredictionListResponse(BaseModel):
    items: list[PredictionResponse]
    total: int
    page: int
    page_size: int


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: uuid.UUID
    image_filename: str
    label: str
    confidence: float
    heatmap_path: str | None
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
