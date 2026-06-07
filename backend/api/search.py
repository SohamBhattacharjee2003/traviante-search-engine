"""Core search endpoints — image and text, sharing one ranking pipeline.

The actual ranking lives in ``core.search_engine`` so the conversational
concierge (``core/chat_agent.py``) reuses the exact same logic.
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.deps import get_encoder, get_metadata_store, get_vector_store
from core.clip_encoder import ClipEncoder
from core.config import Settings, get_settings
from core.metadata_store import MetadataStore
from core.search_engine import rank_image, rank_text
from core.vector_store import VectorStore
from models.destination import (
    SearchFilters,
    SearchResponse,
    SearchType,
    TextSearchRequest,
    TravelStyle,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


def _validate_upload(file: UploadFile, data: bytes, settings: Settings) -> None:
    if file.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported type '{file.content_type}'. Use JPEG, PNG or WEBP.",
        )
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.max_upload_bytes // (1024 * 1024)}MB limit.",
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload."
        )


@router.post("/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    budget_max: int | None = Form(default=None),
    month: str | None = Form(default=None),
    style: TravelStyle | None = Form(default=None),
    group_size: int | None = Form(default=None),
    session_id: str | None = Form(default=None),
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_store: MetadataStore = Depends(get_metadata_store),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    started = time.perf_counter()
    data = await file.read()
    _validate_upload(file, data, settings)

    filters = SearchFilters(
        budget_max=budget_max, month=month, style=style, group_size=group_size
    )
    embedding = encoder.encode_image(data)
    results = rank_image(
        embedding, filters, vector_store, metadata_store, settings.default_top_k
    )
    elapsed = int((time.perf_counter() - started) * 1000)

    metadata_store.log_search(
        {
            "search_type": SearchType.image.value,
            "query_text": None,
            "filters": filters.model_dump(mode="json", exclude_none=True),
            "result_ids": [r.id for r in results],
            "session_id": session_id,
        }
    )
    return SearchResponse(
        results=results,
        total=len(results),
        query_time_ms=elapsed,
        search_type=SearchType.image,
        filters=filters,
        mock_mode=settings.mock_mode,
    )


@router.post("/text", response_model=SearchResponse)
async def search_by_text(
    payload: TextSearchRequest,
    session_id: str | None = None,
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_store: MetadataStore = Depends(get_metadata_store),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    started = time.perf_counter()
    filters = payload.to_filters()
    # Blend lexical + semantic: a typed destination name should win outright,
    # while a "vibe" query rides on CLIP. When CLIP is mocked its hash vectors are
    # meaningless, so skip the semantic signal and rank purely on lexical overlap.
    embedding = None if encoder.is_mock else encoder.encode_text(payload.query)
    results = rank_text(
        payload.query,
        embedding,
        filters,
        vector_store,
        metadata_store,
        settings.default_top_k,
    )
    elapsed = int((time.perf_counter() - started) * 1000)

    metadata_store.log_search(
        {
            "search_type": SearchType.text.value,
            "query_text": payload.query,
            "filters": filters.model_dump(mode="json", exclude_none=True),
            "result_ids": [r.id for r in results],
            "session_id": session_id,
        }
    )
    return SearchResponse(
        results=results,
        total=len(results),
        query_time_ms=elapsed,
        search_type=SearchType.text,
        query_text=payload.query,
        filters=filters,
        mock_mode=settings.mock_mode,
    )
