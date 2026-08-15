"""
Chat service — orchestrates session persistence + RAG turns.

prediction_id is now a real column on ChatSession (see migration
7f3a9c1b6e42), so a session's linked prediction/image survives closing and
reopening the app -- it's stored once at session-start time and reused for
every later message in that session, both for RAG grounding and so the
frontend can keep showing the linked X-ray.
"""

from __future__ import annotations
import uuid

from app.core.exceptions import NotFoundError
from app.models.chat import ChatSession, ChatMessage
from app.repositories.chat_repository import ChatSessionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.rag_client import RagClient


class ChatService:
    def __init__(
        self,
        chat_repository: ChatSessionRepository,
        prediction_repository: PredictionRepository,
        rag_client: RagClient,
    ):
        self.chat_repository = chat_repository
        self.prediction_repository = prediction_repository
        self.rag_client = rag_client

    def start_session(self, user_id: uuid.UUID, prediction_id: uuid.UUID | None) -> ChatSession:
        title = None
        if prediction_id is not None:
            prediction = self.prediction_repository.get_for_user(prediction_id, user_id)
            if prediction is None:
                raise NotFoundError("Prediction not found.")
            title = f"{prediction.label} — {prediction.confidence:.1f}% confidence"

        return self.chat_repository.create(
            ChatSession(user_id=user_id, title=title, prediction_id=prediction_id)
        )

    def list_sessions(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> list[ChatSession]:
        return self.chat_repository.list_for_user(user_id, skip=skip, limit=limit)

    def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession:
        session = self.get_session(session_id, user_id)
        self.chat_repository.delete(session)
        return session

    def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession:
        session = self.chat_repository.get_for_user(session_id, user_id)
        if session is None:
            raise NotFoundError("Chat session not found.")
        return session

    def list_messages(self, session_id: uuid.UUID, user_id: uuid.UUID) -> list[ChatMessage]:
        self.get_session(session_id, user_id)  # ownership check
        return self.chat_repository.list_messages(session_id)

    def send_message(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        prediction_id: uuid.UUID | None = None,
    ):
        session = self.get_session(session_id, user_id)  # ownership check

        # Auto-title sessions that aren't linked to a prediction (those
        # already get a "Label -- confidence%" title in start_session).
        # A generic "New conversation" for every general-question chat made
        # the sidebar unusable once there were more than a couple -- title
        # it from the first real message instead, same pattern ChatGPT/
        # Claude use, so "what is pneumonia" becomes findable at a glance.
        if session.title is None:
            session.title = self._generate_title(message)
            self.chat_repository.update(session)

        # Prefer the session's own stored prediction_id -- the frontend no
        # longer needs to resend it on every message now that it's
        # persisted. An explicit prediction_id argument (e.g. a client that
        # hasn't been updated yet) still overrides it for backward compat.
        effective_prediction_id = prediction_id or session.prediction_id

        prediction_context = None
        if effective_prediction_id is not None:
            prediction = self.prediction_repository.get_for_user(effective_prediction_id, user_id)
            if prediction is None:
                raise NotFoundError("Prediction not found.")
            prediction_context = {
                "predicted_class": prediction.label,
                "confidence": prediction.confidence / 100.0,
                "gradcam_region": None,
            }

        self.chat_repository.add_message(session_id, "user", message)
        result = self.rag_client.chat(
            session_id=str(session_id), message=message, prediction_context=prediction_context
        )
        self.chat_repository.add_message(session_id, "assistant", result.answer)
        return result

    def reset_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.get_session(session_id, user_id)  # ownership check
        self.rag_client.reset(str(session_id))

    @staticmethod
    def _generate_title(message: str, max_length: int = 48) -> str:
        """First-message-based title, same approach ChatGPT/Claude use --
        no extra LLM call needed, just clean truncation on a word boundary
        so it doesn't cut off mid-word."""
        cleaned = " ".join(message.strip().split())
        if len(cleaned) <= max_length:
            return cleaned or "New conversation"
        truncated = cleaned[:max_length].rsplit(" ", 1)[0]
        return f"{truncated}…"
