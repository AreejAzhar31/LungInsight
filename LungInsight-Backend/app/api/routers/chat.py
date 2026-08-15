"""
Chat endpoints — session management + conversational turns against the RAG
clinical assistant (Module 4).
"""

from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, get_chat_service
from app.schemas.chat import (
    ChatSessionResponse,
    ChatSessionStartRequest,
    ChatTurnRequest,
    ChatTurnResponse,
    ChatMessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatSessionResponse]:
    sessions = chat_service.list_sessions(current_user.id)
    return [
        ChatSessionResponse(
            id=s.id, prediction_id=s.prediction_id, title=s.title,
            created_at=s.created_at, updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    data: ChatSessionStartRequest,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatSessionResponse:
    session = chat_service.start_session(current_user.id, data.prediction_id)
    return ChatSessionResponse(
        id=session.id, prediction_id=session.prediction_id, title=session.title,
        created_at=session.created_at, updated_at=session.updated_at,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def list_messages(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageResponse]:
    return chat_service.list_messages(session_id, current_user.id)


@router.post("/sessions/{session_id}/messages", response_model=ChatTurnResponse)
def send_message(
    session_id: uuid.UUID,
    data: ChatTurnRequest,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatTurnResponse:
    result = chat_service.send_message(session_id, current_user.id, data.message, data.prediction_id)
    return ChatTurnResponse(
        session_id=session_id,
        answer=result.answer,
        citations=result.citations,
        is_safe=result.is_safe,
        safety_reason=result.safety_reason,
        verification_passed=result.verification_passed,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    chat_service.delete_session(session_id, current_user.id)


@router.post("/sessions/{session_id}/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    chat_service.reset_session(session_id, current_user.id)
