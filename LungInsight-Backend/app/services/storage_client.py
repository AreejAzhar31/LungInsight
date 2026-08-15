"""
Storage client — where uploaded X-ray images are persisted long-term.

Same pattern as InferenceClient/RagClient: an abstract contract, a Local
implementation (current behavior, no external dependency, used by the test
suite and STORAGE_MODE=local), and a Supabase implementation for real cloud
persistence.

IMPORTANT: this does NOT change how inference reads the uploaded file.
FileService still writes a local temp copy first (needed because
InferenceClient.predict() takes a local file path) — this client runs
*after* inference succeeds, uploading that same file to long-term storage
and (in Supabase mode) removing the local copy afterward to avoid keeping
two copies of every image on disk.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger("app.storage_client")


class StorageClient(ABC):
    @abstractmethod
    def persist(self, local_path: str, storage_key: str, content_type: str) -> str:
        """Uploads the file at local_path to long-term storage under
        storage_key. Returns the reference to store in UploadedImage.file_path
        (a local path for LocalStorageClient, an object key for Supabase)."""
        raise NotImplementedError

    @abstractmethod
    def get_signed_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        """Returns a URL the frontend can use to view/download the image."""
        raise NotImplementedError


class LocalStorageClient(StorageClient):
    """Current behavior — the local temp file IS the permanent copy.
    No-op persist (file is already where it needs to be), local static
    path for retrieval."""

    def __init__(self, upload_dir: str, public_path_prefix: str = "/uploads"):
        self.upload_dir = upload_dir
        self.public_path_prefix = public_path_prefix

    def persist(self, local_path: str, storage_key: str, content_type: str) -> str:
        return local_path

    def get_signed_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        filename = Path(file_path).name
        return f"{self.public_path_prefix}/{filename}"


class SupabaseStorageClient(StorageClient):
    """Uploads to a private Supabase Storage bucket using the service_role
    key (full access, backend-only — never expose this key to the
    frontend). Since the bucket is private, retrieval goes through
    time-limited signed URLs rather than public links."""

    def __init__(self, url: str, service_key: str, bucket: str):
        from supabase import create_client  # local import: optional dependency

        self.client = create_client(url, service_key)
        self.bucket = bucket

    def persist(self, local_path: str, storage_key: str, content_type: str) -> str:
        with open(local_path, "rb") as f:
            data = f.read()
        self.client.storage.from_(self.bucket).upload(
            path=storage_key,
            file=data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        # Local temp copy is no longer needed once it's safely in Supabase —
        # this backend does not keep a second copy on local disk.
        try:
            Path(local_path).unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Could not remove local temp file %s after upload: %s", local_path, exc)
        return storage_key

    def get_signed_url(self, file_path: str, expires_in_seconds: int = 3600) -> str:
        result = self.client.storage.from_(self.bucket).create_signed_url(file_path, expires_in_seconds)
        return result["signedURL"] if "signedURL" in result else result.get("signed_url", "")
