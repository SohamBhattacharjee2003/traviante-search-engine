"""One-time offline indexing pipeline — run locally, not on the server.

For each destination it:
  1. Downloads up to 3 images
  2. Encodes each with CLIP → 512-d embedding
  3. Averages the embeddings into one destination vector
  4. Upserts the vector + metadata filters to Pinecone
  5. Saves the full record to Supabase

Usage:
    # 1. Apply db/schema.sql to your Supabase project
    # 2. Fill in scripts/destinations_data.py with your real catalog
    # 3. Set PINECONE_API_KEY / SUPABASE_URL / SUPABASE_KEY in .env
    python -m scripts.index_destinations
"""
from __future__ import annotations

import logging
import sys

from core.clip_encoder import ClipEncoder
from core.config import get_settings
from core.metadata_store import MetadataStore
from core.vector_store import VectorStore
from scripts.destinations_data import DESTINATIONS

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger("indexer")


def main() -> int:
    settings = get_settings()
    if settings.mock_mode:
        logger.warning(
            "Running in MOCK mode — no Pinecone/Supabase configured. "
            "Set credentials in .env to index for real. Continuing as a dry run."
        )

    encoder = ClipEncoder(settings.clip_model_name, settings.clip_device)
    if encoder.is_mock:
        logger.warning(
            "CLIP unavailable — embeddings will be deterministic mock vectors. "
            "Install torch + CLIP (requirements.txt) for real semantic indexing."
        )

    vector_store = VectorStore(settings)
    metadata_store = MetadataStore(settings)

    batch: list = []
    for i, dest in enumerate(DESTINATIONS, start=1):
        logger.info("[%d/%d] Encoding %s (%s)", i, len(DESTINATIONS), dest.id, dest.name)
        try:
            urls = [str(u) for u in dest.images[:3]]
            embedding = encoder.encode_images_averaged(urls)
        except Exception as exc:
            logger.error("  ✗ Failed to encode %s: %s", dest.id, exc)
            continue

        metadata_store.upsert(dest)
        batch.append((dest, embedding))

    upserted = vector_store.upsert_batch(batch)
    logger.info("Done. Indexed %d / %d destinations.", upserted, len(DESTINATIONS))
    logger.info("Pinecone now holds %d vectors.", vector_store.count())
    return 0


if __name__ == "__main__":
    sys.exit(main())
