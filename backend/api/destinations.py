"""Destination management endpoints.

GET  /v1/destinations/        public — list active destinations
POST /v1/destinations/        admin  — create/update + auto-embed + Pinecone upsert

The POST flow is how you add a new destination without re-running the bulk indexing
script: encode its images with CLIP, upsert the vector, and save the full record.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import (
    get_encoder,
    get_metadata_store,
    get_vector_store,
    require_admin_key,
)
from core.clip_encoder import ClipEncoder
from core.metadata_store import MetadataStore
from core.vector_store import VectorStore
from models.destination import Destination, DestinationCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("/", response_model=list[Destination])
async def list_destinations(
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[Destination]:
    return metadata_store.list_active()


@router.post(
    "/",
    response_model=Destination,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_key)],
)
async def create_destination(
    payload: DestinationCreate,
    encoder: ClipEncoder = Depends(get_encoder),
    vector_store: VectorStore = Depends(get_vector_store),
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> Destination:
    if not payload.images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image URL is required to embed the destination.",
        )

    image_urls = [str(u) for u in payload.images[:3]]
    try:
        embedding = encoder.encode_images_averaged(image_urls)
    except Exception as exc:
        logger.exception("Failed to embed destination %s", payload.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not encode images: {exc}",
        ) from exc

    vector_store.upsert(payload, embedding)
    metadata_store.upsert(payload)
    logger.info("Indexed destination '%s'.", payload.id)
    return payload
