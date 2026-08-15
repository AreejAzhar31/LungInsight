"""
Prediction service — orchestrates the upload -> inference -> persistence flow.
"""

from __future__ import annotations
import uuid

from fastapi import UploadFile

from app.core.exceptions import NotFoundError
from app.models.uploaded_image import UploadedImage
from app.models.prediction import Prediction
from app.repositories.uploaded_image_repository import UploadedImageRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.file_service import FileService
from app.services.inference_client import InferenceClient
from app.services.storage_client import StorageClient


class PredictionService:
    def __init__(
        self,
        image_repository: UploadedImageRepository,
        prediction_repository: PredictionRepository,
        file_service: FileService,
        inference_client: InferenceClient,
        storage_client: StorageClient,
    ):
        self.image_repository = image_repository
        self.prediction_repository = prediction_repository
        self.file_service = file_service
        self.inference_client = inference_client
        self.storage_client = storage_client

    async def create_prediction(self, user_id: uuid.UUID, file: UploadFile) -> Prediction:
        stored_filename, file_path, size_bytes = await self.file_service.save(file)

        image = UploadedImage(
            user_id=user_id,
            original_filename=file.filename or stored_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            content_type=file.content_type or "application/octet-stream",
            file_size_bytes=size_bytes,
        )
        image = self.image_repository.create(image)

        # Inference reads the local temp file directly -- must happen before
        # any storage migration, since Supabase mode removes the local copy
        # once it's safely uploaded.
        result = self.inference_client.predict(file_path)

        # Persist to long-term storage (no-op / same path in local mode;
        # actually uploads to Supabase and updates the DB reference in
        # Supabase mode). Runs after inference on purpose -- a storage
        # hiccup here shouldn't block a prediction that already succeeded.
        storage_key = f"{user_id}/{stored_filename}"
        try:
            persisted_path = self.storage_client.persist(file_path, storage_key, image.content_type)
            if persisted_path != image.file_path:
                image.file_path = persisted_path
                self.image_repository.update(image)
        except Exception as exc:  # noqa: BLE001
            # Cloud storage failing shouldn't fail the whole prediction --
            # the local temp copy still exists in this case, just not
            # migrated to long-term storage. Logged for follow-up.
            import logging

            logging.getLogger("app.prediction_service").error(
                "Failed to persist image %s to long-term storage: %s", image.id, exc
            )

        prediction = Prediction(
            user_id=user_id,
            image_id=image.id,
            label=result.label,
            confidence=result.confidence,
            heatmap_path=result.heatmap_path,
        )
        return self.prediction_repository.create(prediction)

    def get_prediction(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> Prediction:
        prediction = self.prediction_repository.get_for_user(prediction_id, user_id)
        if prediction is None:
            raise NotFoundError("Prediction not found.")
        return prediction

    def get_image_url(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> str:
        prediction = self.get_prediction(prediction_id, user_id)
        image = self.image_repository.get_for_user(prediction.image_id, user_id)
        if image is None:
            raise NotFoundError("Uploaded image not found.")
        return self.storage_client.get_signed_url(image.file_path)

    def list_predictions(self, user_id: uuid.UUID, page: int, page_size: int) -> tuple[list[Prediction], int]:
        skip = (page - 1) * page_size
        items = self.prediction_repository.list_for_user(user_id, skip=skip, limit=page_size)
        total = self.prediction_repository.count_for_user(user_id)
        return items, total

    def get_history(self, user_id: uuid.UUID, page: int, page_size: int):
        skip = (page - 1) * page_size
        rows = self.prediction_repository.history_for_user(user_id, skip=skip, limit=page_size)
        total = self.prediction_repository.count_for_user(user_id)
        return rows, total
