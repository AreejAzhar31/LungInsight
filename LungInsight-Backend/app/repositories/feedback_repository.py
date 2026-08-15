"""Feedback repository."""

from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    def __init__(self, db: Session):
        super().__init__(db, Feedback)
