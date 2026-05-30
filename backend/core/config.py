"""Centralised configuration.

All settings are read from environment variables (or a local ``.env`` file) via
pydantic-settings. The service degrades gracefully into **mock mode** when external
credentials are absent so the whole stack can run locally with no accounts.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── App ────────────────────────────────────────────────────────────────
    app_name: str = "Traviante Visual Search"
    environment: str = Field(default="development")
    api_v1_prefix: str = "/v1"

    # CORS — comma separated origins allowed to call the API.
    cors_origins: str = Field(
        default="http://localhost:3000,https://traviante.com"
    )

    # ── Auth ───────────────────────────────────────────────────────────────
    # Shared secret the Next.js proxy sends, and the admin key for write ops.
    api_key: str = Field(default="dev-frontend-key")
    admin_api_key: str = Field(default="dev-admin-key")

    # ── CLIP ───────────────────────────────────────────────────────────────
    clip_model_name: str = Field(default="ViT-B/32")
    clip_device: str = Field(default="auto")  # auto | cpu | cuda
    embedding_dim: int = 512

    # ── Pinecone ───────────────────────────────────────────────────────────
    pinecone_api_key: str | None = Field(default=None)
    pinecone_index_name: str = Field(default="traviante-destinations")
    pinecone_cloud: str = Field(default="aws")
    pinecone_region: str = Field(default="us-east-1")

    # ── Supabase ───────────────────────────────────────────────────────────
    supabase_url: str | None = Field(default=None)
    supabase_key: str | None = Field(default=None)

    # ── Uploads ────────────────────────────────────────────────────────────
    max_upload_bytes: int = 5 * 1024 * 1024  # 5 MB
    allowed_image_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )
    default_top_k: int = 5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def pinecone_enabled(self) -> bool:
        return bool(self.pinecone_api_key)

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def mock_mode(self) -> bool:
        """True when running without external data services."""
        return not (self.pinecone_enabled and self.supabase_enabled)


@lru_cache
def get_settings() -> Settings:
    return Settings()
