"""Prediction endpoints: create, get by id, list."""

from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.dependencies import get_prediction_service, CurrentUser
from app.schemas.prediction import PredictionResponse, PredictionListResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/v1", tags=["Predictions"])


@router.post("/prediction", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    prediction = await prediction_service.create_prediction(current_user.id, file)
    return prediction


@router.get("/prediction/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: uuid.UUID,
    current_user: CurrentUser,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    return prediction_service.get_prediction(prediction_id, current_user.id)


@router.get("/prediction/{prediction_id}/image-url")
def get_prediction_image_url(
    prediction_id: uuid.UUID,
    current_user: CurrentUser,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> dict:
    """Returns a viewable URL for the original uploaded X-ray. In local
    storage mode this is a static file path served by this backend; in
    Supabase mode it's a time-limited signed URL (the bucket is private)."""
    url = prediction_service.get_image_url(prediction_id, current_user.id)
    return {"url": url}


@router.get("/predictions", response_model=PredictionListResponse)
def list_predictions(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionListResponse:
    items, total = prediction_service.list_predictions(current_user.id, page, page_size)
    return PredictionListResponse(items=items, total=total, page=page, page_size=page_size)
