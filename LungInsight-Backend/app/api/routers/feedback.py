"""Feedback endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_feedback_service, CurrentUser
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/api/v1", tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    data: FeedbackCreate,
    current_user: CurrentUser,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    return feedback_service.create_feedback(current_user.id, data)
