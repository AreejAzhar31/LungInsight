"""User repository — data access for the users table."""

from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None
