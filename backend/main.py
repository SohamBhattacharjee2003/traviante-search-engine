"""FastAPI application entry point.

Heavy services are built **once** in the lifespan handler (CLIP takes ~3s to load but
~50ms per inference) and stashed on ``app.state`` so every request reuses them.
"""
from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import destinations, health, search
from core.clip_encoder import ClipEncoder
from core.config import get_settings
from core.metadata_store import MetadataStore
from core.vector_store import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("traviante")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting %s  [env=%s, mock_mode=%s]",
        settings.app_name,
        settings.environment,
        settings.mock_mode,
    )

    encoder = ClipEncoder(settings.clip_model_name, settings.clip_device)
    vector_store = VectorStore(settings)
    metadata_store = MetadataStore(settings)

    # In mock mode, seed the bundled sample catalog so search returns real cards.
    if settings.mock_mode:
        from scripts.destinations_data import DESTINATIONS

        metadata_store.seed(DESTINATIONS)
        for dest in DESTINATIONS:
            embedding = None
            if not encoder.is_mock and dest.images:
                try:
                    embedding = encoder.encode_images_averaged(
                        [str(u) for u in dest.images]
                    )
                except Exception as exc:  # a bad image URL must not crash startup
                    logger.warning(
                        "Image embed failed for %s (%s); falling back to text.",
                        dest.id, exc,
                    )
            if embedding is None:
                # No real CLIP, no photo, or the download failed: embed the text so
                # the destination stays searchable (CLIP shares one image/text space).
                embedding = encoder.encode_text(dest.description or dest.name)
            vector_store.upsert(dest, embedding)
        logger.info("Mock index ready with %d destinations.", vector_store.count())

    app.state.encoder = encoder
    app.state.vector_store = vector_store
    app.state.metadata_store = metadata_store
    yield
    logger.info("Shutting down.")


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Multimodal (image + text) destination search powered by CLIP.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(destinations.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }


if __name__ == "__main__":
    # Convenience entry so `python main.py` works as well as `uvicorn main:app`.
    import os

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=settings.environment == "development",
    )
