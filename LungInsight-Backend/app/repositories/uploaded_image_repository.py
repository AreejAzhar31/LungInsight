"""UploadedImage repository."""

from __future__ import annotations
import uuid
from sqlalchemy.orm import Session

from app.models.uploaded_image import UploadedImage
from app.repositories.base import BaseRepository


class UploadedImageRepository(BaseRepository[UploadedImage]):
    def __init__(self, db: Session):
        super().__init__(db, UploadedImage)

    def get_for_user(self, image_id: uuid.UUID, user_id: uuid.UUID) -> UploadedImage | None:
        return (
            self.db.query(UploadedImage)
            .filter(UploadedImage.id == image_id, UploadedImage.user_id == user_id)
            .first()
        )
