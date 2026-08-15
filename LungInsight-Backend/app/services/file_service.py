"""
File service — validates and persists uploaded images to local disk.

Validates both the declared content-type AND actual file size (streamed,
so a mislabeled huge file can't exhaust memory). Swap `_save_to_disk` for
an S3/blob-storage call in production without touching callers.
"""

from __future__ import annotations
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import InvalidFileError

settings = get_settings()


class FileService:
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, file: UploadFile) -> None:
        if file.content_type not in settings.allowed_image_types_list:
            raise InvalidFileError(
                f"Unsupported file type '{file.content_type}'. "
                f"Allowed types: {', '.join(settings.allowed_image_types_list)}"
            )

    async def save(self, file: UploadFile) -> tuple[str, str, int]:
        """
        Validates, streams to disk with a random filename (never trusts the
        client-supplied filename), and returns (stored_filename, file_path, size_bytes).
        """
        self.validate(file)

        extension = Path(file.filename or "").suffix.lower() or ".jpg"
        stored_filename = f"{uuid.uuid4()}{extension}"
        destination = self.upload_dir / stored_filename

        size_bytes = 0
        max_bytes = settings.max_upload_size_bytes

        with open(destination, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    out_file.close()
                    destination.unlink(missing_ok=True)
                    raise InvalidFileError(
                        f"File exceeds the maximum allowed size of {settings.max_upload_size_mb}MB."
                    )
                out_file.write(chunk)

        if size_bytes == 0:
            destination.unlink(missing_ok=True)
            raise InvalidFileError("Uploaded file is empty.")

        return stored_filename, str(destination), size_bytes
