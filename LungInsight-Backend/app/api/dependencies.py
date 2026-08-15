"""
Dependency injection wiring.

Every repository/service is constructed here via FastAPI's `Depends()`
chain, per-request, from a fresh DB session. Routers only ever depend on
services — never on repositories or the DB session directly.
"""

from __future__ import annotations
from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token, InvalidTokenError as JWTInvalidTokenError
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.uploaded_image_repository import UploadedImageRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.log_repository import LogRepository
from app.repositories.chat_repository import ChatSessionRepository
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from app.core.config import get_settings
from app.services.inference_client import InferenceClient, StubInferenceClient, HttpInferenceClient
from app.services.rag_client import RagClient, StubRagClient, HttpRagClient
from app.services.storage_client import StorageClient, LocalStorageClient, SupabaseStorageClient
from app.services.prediction_service import PredictionService
from app.services.feedback_service import FeedbackService
from app.services.log_service import LogService
from app.services.chat_service import ChatService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


# ---- repositories --------------------------------------------------------

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_image_repository(db: Session = Depends(get_db)) -> UploadedImageRepository:
    return UploadedImageRepository(db)


def get_prediction_repository(db: Session = Depends(get_db)) -> PredictionRepository:
    return PredictionRepository(db)


def get_feedback_repository(db: Session = Depends(get_db)) -> FeedbackRepository:
    return FeedbackRepository(db)


def get_log_repository(db: Session = Depends(get_db)) -> LogRepository:
    return LogRepository(db)


def get_chat_repository(db: Session = Depends(get_db)) -> ChatSessionRepository:
    return ChatSessionRepository(db)


# ---- services --------------------------------------------------------

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


def get_file_service() -> FileService:
    return FileService()


def get_inference_client() -> InferenceClient:
    """
    Returns the stub (default, used by the test suite) or the real HTTP
    client that calls the Module 1 model-serving microservice, based on
    INFERENCE_MODE in .env. Switching modes never requires touching
    PredictionService or any router — same contract either way.
    """
    settings = get_settings()
    if settings.inference_mode == "http":
        return HttpInferenceClient(
            base_url=settings.inference_service_url,
            heatmap_dir=settings.heatmap_dir,
            timeout_seconds=settings.inference_timeout_seconds,
        )
    return StubInferenceClient()


def get_storage_client() -> StorageClient:
    """Returns the local no-op client (default, used by the test suite) or
    the real Supabase client, based on STORAGE_MODE in .env."""
    settings = get_settings()
    if settings.storage_mode == "supabase":
        return SupabaseStorageClient(
            url=settings.supabase_url,
            service_key=settings.supabase_service_key,
            bucket=settings.supabase_bucket,
        )
    return LocalStorageClient(upload_dir=settings.upload_dir)


def get_prediction_service(
    image_repo: UploadedImageRepository = Depends(get_image_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    file_service: FileService = Depends(get_file_service),
    inference_client: InferenceClient = Depends(get_inference_client),
    storage_client: StorageClient = Depends(get_storage_client),
) -> PredictionService:
    return PredictionService(image_repo, prediction_repo, file_service, inference_client, storage_client)


def get_feedback_service(
    feedback_repo: FeedbackRepository = Depends(get_feedback_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
) -> FeedbackService:
    return FeedbackService(feedback_repo, prediction_repo)


def get_log_service(log_repo: LogRepository = Depends(get_log_repository)) -> LogService:
    return LogService(log_repo)


def get_rag_client() -> RagClient:
    """Returns the stub (default, used by the test suite) or the real HTTP
    client that calls the Module 4 RAG microservice, based on RAG_MODE in
    .env. Mirrors get_inference_client()'s stub/http switch exactly."""
    settings = get_settings()
    if settings.rag_mode == "http":
        return HttpRagClient(base_url=settings.rag_service_url, timeout_seconds=settings.rag_timeout_seconds)
    return StubRagClient()


def get_chat_service(
    chat_repo: ChatSessionRepository = Depends(get_chat_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    rag_client: RagClient = Depends(get_rag_client),
) -> ChatService:
    return ChatService(chat_repo, prediction_repo, rag_client)


# ---- auth: current user --------------------------------------------------

def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error

    try:
        payload = decode_token(token, expected_type="access")
    except JWTInvalidTokenError:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    try:
        user = user_repo.get(uuid.UUID(user_id))
    except (ValueError, TypeError):
        raise credentials_error

    if user is None or not user.is_active:
        raise credentials_error

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
