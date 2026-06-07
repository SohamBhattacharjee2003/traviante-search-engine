"""Conversational concierge endpoints.

``POST /v1/chat``        — a text turn in the conversation.
``POST /v1/chat/image``  — an image turn: the user uploads a photo mid-chat and
                            the concierge narrates the visual matches.

Both reuse the same ranking pipeline as ``/v1/search`` (via ``core.search_engine``),
so the chatbot and the raw search API can never drift apart.
"""
from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from api.deps import (
    get_chat_agent,
    get_encoder,
    get_metadata_store,
    get_vector_store,
)
from core.chat_agent import ChatAgent
from core.clip_encoder import ClipEncoder
from core.config import Settings, get_settings
from core.metadata_store import MetadataStore
from core.search_engine import rank_image
from core.vector_store import VectorStore
from models.destination import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    SearchFilters,
    SearchType,
    TravelStyle,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session_id: str | None = None,
    agent: ChatAgent = Depends(get_chat_agent),
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> ChatResponse:
    response = await agent.respond_text(
        payload.message,
        payload.history,
        payload.filters,
        encoder,
        vector_store,
        metadata_store,
    )
    metadata_store.log_search(
        {
            "search_type": SearchType.text.value,
            "query_text": payload.message,
            "filters": response.filters.model_dump(mode="json", exclude_none=True),
            "result_ids": [r.id for r in response.results],
            "session_id": session_id or payload.session_id,
        }
    )
    return response


@router.post("/image", response_model=ChatResponse)
async def chat_image(
    file: UploadFile = File(...),
    history: str = Form(default="[]"),
    caption: str = Form(default=""),
    budget_max: int | None = Form(default=None),
    month: str | None = Form(default=None),
    style: TravelStyle | None = Form(default=None),
    session_id: str | None = Form(default=None),
    agent: ChatAgent = Depends(get_chat_agent),
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_store: MetadataStore = Depends(get_metadata_store),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    started = time.perf_counter()
    data = await file.read()
    _validate_upload(file, data, settings)

    try:
        raw_history = json.loads(history) if history else []
        parsed_history = [ChatMessage.model_validate(m) for m in raw_history][-12:]
    except (json.JSONDecodeError, ValidationError):
        parsed_history = []

    filters = SearchFilters(budget_max=budget_max, month=month, style=style)
    embedding = encoder.encode_image(data)
    results = rank_image(
        embedding, filters, vector_store, metadata_store, settings.default_top_k
    )

    response = await agent.respond_image(results, caption, parsed_history, filters, started)
    metadata_store.log_search(
        {
            "search_type": SearchType.image.value,
            "query_text": caption or None,
            "filters": filters.model_dump(mode="json", exclude_none=True),
            "result_ids": [r.id for r in results],
            "session_id": session_id,
        }
    )
    return response


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
