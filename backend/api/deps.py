"""Shared FastAPI dependencies — service accessors and auth guards.

The heavy services (CLIP, Pinecone, Supabase) are constructed once at startup in
``main.py`` and stashed on ``app.state``. These helpers pull them off the request so
routers stay thin and testable.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status

from core.clip_encoder import ClipEncoder
from core.config import Settings, get_settings
from core.metadata_store import MetadataStore
from core.vector_store import VectorStore


def get_encoder(request: Request) -> ClipEncoder:
    return request.app.state.encoder


def get_vector_store(request: Request) -> VectorStore:
    return request.app.state.vector_store


def get_metadata_store(request: Request) -> MetadataStore:
    return request.app.state.metadata_store


def require_admin_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Guard write endpoints with the admin API key."""
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key.",
        )
