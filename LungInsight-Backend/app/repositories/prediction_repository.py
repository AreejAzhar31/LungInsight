"""Prediction repository."""

from __future__ import annotations
import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.uploaded_image import UploadedImage
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, db: Session):
        super().__init__(db, Prediction)

    def get_for_user(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> Prediction | None:
        return (
            self.db.query(Prediction)
            .filter(Prediction.id == prediction_id, Prediction.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[Prediction]:
        return (
            self.db.query(Prediction)
            .filter(Prediction.user_id == user_id)
            .order_by(Prediction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_for_user(self, user_id: uuid.UUID) -> int:
        return self.db.query(func.count(Prediction.id)).filter(Prediction.user_id == user_id).scalar() or 0

    def history_for_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20):
        """Predictions joined with their source image, newest first."""
        return (
            self.db.query(Prediction, UploadedImage)
            .join(UploadedImage, Prediction.image_id == UploadedImage.id)
            .filter(Prediction.user_id == user_id)
            .order_by(Prediction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
