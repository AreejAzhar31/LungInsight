"""Feedback service."""

from __future__ import annotations
import uuid

from app.core.exceptions import NotFoundError
from app.models.feedback import Feedback
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.feedback import FeedbackCreate


class FeedbackService:
    def __init__(self, feedback_repository: FeedbackRepository, prediction_repository: PredictionRepository):
        self.feedback_repository = feedback_repository
        self.prediction_repository = prediction_repository

    def create_feedback(self, user_id: uuid.UUID, data: FeedbackCreate) -> Feedback:
        prediction = self.prediction_repository.get_for_user(data.prediction_id, user_id)
        if prediction is None:
            raise NotFoundError("Prediction not found.")

        feedback = Feedback(
            user_id=user_id,
            prediction_id=data.prediction_id,
            rating=data.rating,
            comment=data.comment,
        )
        return self.feedback_repository.create(feedback)
