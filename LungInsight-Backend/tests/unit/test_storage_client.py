"""Tests for StorageClient implementations."""
from unittest.mock import MagicMock, patch

from app.services.storage_client import LocalStorageClient, SupabaseStorageClient


def test_local_storage_persist_is_noop(tmp_path):
    client = LocalStorageClient(upload_dir=str(tmp_path))
    local_file = tmp_path / "xray.jpg"
    local_file.write_bytes(b"fake image bytes")

    result = client.persist(str(local_file), "some-key", "image/jpeg")

    assert result == str(local_file)
    assert local_file.exists()  # local mode never deletes the file


def test_local_storage_signed_url_returns_static_path(tmp_path):
    client = LocalStorageClient(upload_dir=str(tmp_path), public_path_prefix="/uploads")
    url = client.get_signed_url(str(tmp_path / "xray.jpg"))
    assert url == "/uploads/xray.jpg"


def test_supabase_persist_uploads_and_deletes_local_copy(tmp_path):
    local_file = tmp_path / "xray.jpg"
    local_file.write_bytes(b"fake image bytes")

    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase

        client = SupabaseStorageClient(url="https://fake.supabase.co", service_key="fake-key", bucket="test-bucket")
        result = client.persist(str(local_file), "user123/xray.jpg", "image/jpeg")

        # Uploaded to the right bucket with the right key
        mock_supabase.storage.from_.assert_any_call("test-bucket")
        upload_call = mock_supabase.storage.from_.return_value.upload
        assert upload_call.call_args.kwargs["path"] == "user123/xray.jpg"

        # Returns the storage key, not the local path
        assert result == "user123/xray.jpg"

        # Local temp copy is cleaned up after a successful upload
        assert not local_file.exists()


def test_supabase_get_signed_url(tmp_path):
    with patch("supabase.create_client") as mock_create_client:
        mock_supabase = MagicMock()
        mock_supabase.storage.from_.return_value.create_signed_url.return_value = {
            "signedURL": "https://fake.supabase.co/signed/xray.jpg?token=abc"
        }
        mock_create_client.return_value = mock_supabase

        client = SupabaseStorageClient(url="https://fake.supabase.co", service_key="fake-key", bucket="test-bucket")
        url = client.get_signed_url("user123/xray.jpg")

        assert url == "https://fake.supabase.co/signed/xray.jpg?token=abc"
