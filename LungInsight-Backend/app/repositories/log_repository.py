"""Log repository."""

from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.log import Log
from app.repositories.base import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self, db: Session):
        super().__init__(db, Log)
