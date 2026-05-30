"""Health + readiness endpoint — surfaces which services are live vs mocked."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_encoder, get_vector_store
from core.clip_encoder import ClipEncoder
from core.config import Settings, get_settings
from core.vector_store import VectorStore
from models.destination import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        clip_model=settings.clip_model_name,
        clip_device=f"{encoder.device}{' (mock)' if encoder.is_mock else ''}",
        pinecone_enabled=settings.pinecone_enabled,
        supabase_enabled=settings.supabase_enabled,
        mock_mode=settings.mock_mode,
        indexed_vectors=vector_store.count(),
    )
