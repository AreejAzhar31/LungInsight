"""Integration tests for PredictionService (service + repository + DB, no HTTP)."""
import io
import uuid
import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.repositories.uploaded_image_repository import UploadedImageRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.user_repository import UserRepository
from app.services.prediction_service import PredictionService
from app.services.file_service import FileService
from app.services.inference_client import StubInferenceClient
from app.services.storage_client import LocalStorageClient
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister
from app.core.exceptions import NotFoundError


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def user(session):
    user, _ = AuthService(UserRepository(session)).register(
        UserRegister(email="pred_user@example.com", password="SecurePass123")
    )
    return user


@pytest.fixture()
def prediction_service(session, tmp_path):
    return PredictionService(
        image_repository=UploadedImageRepository(session),
        prediction_repository=PredictionRepository(session),
        file_service=FileService(upload_dir=str(tmp_path)),
        inference_client=StubInferenceClient(),
        storage_client=LocalStorageClient(upload_dir=str(tmp_path)),
    )


def _upload_file() -> UploadFile:
    return UploadFile(
        filename="xray.jpg", file=io.BytesIO(b"\xff\xd8fakejpeg"), headers={"content-type": "image/jpeg"}
    )


@pytest.mark.asyncio
async def test_create_prediction_persists_image_and_prediction(prediction_service, user):
    prediction = await prediction_service.create_prediction(user.id, _upload_file())
    assert prediction.label in ("Normal", "Pneumonia")
    assert prediction.user_id == user.id
    assert prediction.image_id is not None


def test_get_prediction_not_found_raises(prediction_service, user):
    with pytest.raises(NotFoundError):
        prediction_service.get_prediction(uuid.uuid4(), user.id)


@pytest.mark.asyncio
async def test_get_prediction_wrong_user_raises_not_found(prediction_service, user, session):
    prediction = await prediction_service.create_prediction(user.id, _upload_file())
    other_user, _ = AuthService(UserRepository(session)).register(
        UserRegister(email="other@example.com", password="SecurePass123")
    )
    with pytest.raises(NotFoundError):
        prediction_service.get_prediction(prediction.id, other_user.id)


@pytest.mark.asyncio
async def test_list_predictions_pagination(prediction_service, user):
    for _ in range(3):
        await prediction_service.create_prediction(user.id, _upload_file())

    items, total = prediction_service.list_predictions(user.id, page=1, page_size=2)
    assert total == 3
    assert len(items) == 2


@pytest.mark.asyncio
async def test_history_returns_joined_image_data(prediction_service, user):
    await prediction_service.create_prediction(user.id, _upload_file())
    rows, total = prediction_service.get_history(user.id, page=1, page_size=10)
    assert total == 1
    prediction, image = rows[0]
    assert image.original_filename == "xray.jpg"
