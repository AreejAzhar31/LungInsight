"""
Centralized application configuration.

All settings are loaded from environment variables (or a `.env` file in
development). Never hardcode secrets — everything here is overridable via
the environment, per twelve-factor-app conventions.
"""

from __future__ import annotations
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "LungInsight AI Backend"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/lunginsight"

    # JWT
    jwt_secret_key: str = "change-this-to-a-long-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # File uploads
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png,image/jpg"

    # Rate limiting
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "5/minute"

    # AI model inference
    # "stub" (default) keeps the backend fully runnable/testable on its own,
    # matching the existing test suite. Set to "http" once the model
    # service (ai/service/main.py) is running to get real predictions.
    inference_mode: str = "stub"
    inference_service_url: str = "http://localhost:8500"
    inference_timeout_seconds: float = 30.0
    heatmap_dir: str = "uploads/heatmaps"

    # RAG chat service
    # "stub" (default) keeps the backend fully runnable/testable on its own,
    # matching the existing test suite. Set to "http" once the RAG service
    # (rag/api.py) is running to get real, retrieval-grounded chat answers.
    rag_mode: str = "stub"
    rag_service_url: str = "http://localhost:8600"
    rag_timeout_seconds: float = 60.0

    # Long-term image storage
    # "local" (default) keeps uploaded images on this machine's disk --
    # what the test suite uses, zero external dependencies. Set to
    # "supabase" to persist uploads to Supabase Storage instead.
    storage_mode: str = "local"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_bucket: str = "lunginsight-uploads"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_image_types_list(self) -> list[str]:
        return [t.strip() for t in self.allowed_image_types.split(",") if t.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — env is only parsed once per process."""
    return Settings()
