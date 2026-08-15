"""Unit tests for app.services.file_service."""
import io
import pytest
from fastapi import UploadFile

from app.services.file_service import FileService
from app.core.exceptions import InvalidFileError


@pytest.fixture()
def file_service(tmp_path):
    return FileService(upload_dir=str(tmp_path))


def _make_upload_file(content: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content), headers={"content-type": content_type})


def test_validate_accepts_allowed_type(file_service):
    upload = _make_upload_file(b"data", "x.jpg", "image/jpeg")
    file_service.validate(upload)  # should not raise


def test_validate_rejects_disallowed_type(file_service):
    upload = _make_upload_file(b"data", "x.txt", "text/plain")
    with pytest.raises(InvalidFileError):
        file_service.validate(upload)


@pytest.mark.asyncio
async def test_save_writes_file_and_returns_metadata(file_service, tmp_path):
    content = b"\xff\xd8\xff fake jpeg bytes"
    upload = _make_upload_file(content, "xray.jpg", "image/jpeg")

    stored_filename, file_path, size = await file_service.save(upload)

    assert size == len(content)
    assert (tmp_path / stored_filename).exists()
    assert stored_filename != "xray.jpg"  # never trusts client filename directly
    assert file_path.endswith(stored_filename)


@pytest.mark.asyncio
async def test_save_rejects_empty_file(file_service):
    upload = _make_upload_file(b"", "empty.jpg", "image/jpeg")
    with pytest.raises(InvalidFileError):
        await file_service.save(upload)


@pytest.mark.asyncio
async def test_save_enforces_max_size(file_service, monkeypatch):
    from app.core import config as config_module
    settings = config_module.get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)  # ~0MB limit forces rejection
    # max_upload_size_bytes is a property computed from max_upload_size_mb; patch directly instead
    monkeypatch.setattr(
        type(settings), "max_upload_size_bytes", property(lambda self: 5)
    )

    content = b"x" * 1000
    upload = _make_upload_file(content, "big.jpg", "image/jpeg")
    with pytest.raises(InvalidFileError):
        await file_service.save(upload)
