"""Core search endpoints — image and text, sharing one ranking pipeline."""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.deps import get_encoder, get_metadata_store, get_vector_store
from core.clip_encoder import ClipEncoder
from core.config import Settings, get_settings
from core.metadata_store import MetadataStore
from core.vector_store import VectorStore
from models.destination import (
    DestinationResult,
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


def _rank(
    embedding: list[float],
    filters: SearchFilters,
    vector_store: VectorStore,
    metadata_store: MetadataStore,
    top_k: int,
) -> list[DestinationResult]:
    """Vector search → fetch metadata in ranked order → assemble result objects."""
    matches = vector_store.query(embedding, top_k=top_k, filters=filters)
    if not matches:
        return []

    ids = [m[0] for m in matches]
    scores = {m[0]: m[1] for m in matches}
    destinations = metadata_store.get_by_ids(ids)

    results: list[DestinationResult] = []
    for rank, dest in enumerate(destinations, start=1):
        results.append(
            DestinationResult(
                **dest.model_dump(),
                score=round(scores.get(dest.id, 0.0), 4),
                rank=rank,
                match_reason=_match_reason(dest.travel_styles, filters),
            )
        )
    return results


def _match_reason(styles: list[TravelStyle], filters: SearchFilters) -> str | None:
    if filters.style and filters.style in styles:
        return f"Matches your {filters.style.value} style"
    if styles:
        return f"Great for {styles[0].value}"
    return None


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
    results = _rank(embedding, filters, vector_store, metadata_store, settings.default_top_k)
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
    embedding = encoder.encode_text(payload.query)
    results = _rank(embedding, filters, vector_store, metadata_store, settings.default_top_k)
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
