"""Chat session/message repository."""

from __future__ import annotations
import uuid
from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, db: Session):
        super().__init__(db, ChatSession)

    def get_for_user(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_message(self, session_id: uuid.UUID, role: str, content: str) -> ChatMessage:
        message = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
