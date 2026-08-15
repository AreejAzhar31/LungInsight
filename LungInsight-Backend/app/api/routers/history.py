"""History endpoint — predictions joined with their source image."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_prediction_service, CurrentUser
from app.schemas.prediction import HistoryResponse, HistoryItem
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/v1", tags=["History"])


@router.get("/history", response_model=HistoryResponse)
def get_history(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> HistoryResponse:
    rows, total = prediction_service.get_history(current_user.id, page, page_size)
    items = [
        HistoryItem(
            prediction_id=prediction.id,
            image_filename=image.original_filename,
            label=prediction.label,
            confidence=prediction.confidence,
            heatmap_path=prediction.heatmap_path,
            created_at=prediction.created_at,
        )
        for prediction, image in rows
    ]
    return HistoryResponse(items=items, total=total, page=page, page_size=page_size)
