"""Pinecone Serverless wrapper.

Stores the 512-d CLIP embeddings and runs cosine-similarity search with metadata
filters applied *before* ranking (fast). When Pinecone is not configured the store
falls back to an **in-memory brute-force index** so search works locally.

Metadata stored per vector (kept small — Pinecone's per-vector metadata cap is 40KB):
    price_min, price_max, months[], styles[]
Rich fields (description, images, highlights) live in Supabase instead.
"""
from __future__ import annotations

import logging

import numpy as np

from core.config import Settings
from models.destination import Destination, SearchFilters

logger = logging.getLogger(__name__)

Match = tuple[str, float]  # (id, score)


def _vector_metadata(dest: Destination) -> dict:
    return {
        "price_min": dest.price_min_inr,
        "price_max": dest.price_max_inr,
        "months": [m.lower() for m in dest.best_months],
        "styles": [s.value for s in dest.travel_styles],
    }


def _build_pinecone_filter(filters: SearchFilters) -> dict | None:
    """Translate SearchFilters into Pinecone filter syntax."""
    f: dict = {}
    if filters.budget_max is not None:
        # Destination's entry price must be within the user's budget.
        f["price_min"] = {"$lte": filters.budget_max}
    if filters.month:
        f["months"] = {"$in": [filters.month.lower()]}
    if filters.style:
        f["styles"] = {"$in": [filters.style.value]}
    return f or None


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._index = None
        self.is_mock = not settings.pinecone_enabled
        # in-memory fallback: id -> (np.ndarray, metadata)
        self._mem: dict[str, tuple[np.ndarray, dict]] = {}
        if not self.is_mock:
            self._connect()

    # ── connection ─────────────────────────────────────────────────────────
    def _connect(self) -> None:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=self.settings.pinecone_api_key)
        name = self.settings.pinecone_index_name
        existing = {i["name"] for i in pc.list_indexes()}
        if name not in existing:
            logger.info("Creating Pinecone index '%s'...", name)
            pc.create_index(
                name=name,
                dimension=self.settings.embedding_dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.settings.pinecone_cloud,
                    region=self.settings.pinecone_region,
                ),
            )
        self._index = pc.Index(name)
        logger.info("Connected to Pinecone index '%s'.", name)

    # ── writes ─────────────────────────────────────────────────────────────
    def upsert(self, dest: Destination, embedding: list[float]) -> None:
        metadata = _vector_metadata(dest)
        if self.is_mock:
            self._mem[dest.id] = (np.asarray(embedding, dtype=np.float32), metadata)
            return
        self._index.upsert(
            vectors=[{"id": dest.id, "values": embedding, "metadata": metadata}]
        )

    def upsert_batch(
        self, items: list[tuple[Destination, list[float]]]
    ) -> int:
        if self.is_mock:
            for dest, emb in items:
                self.upsert(dest, emb)
            return len(items)
        vectors = [
            {"id": d.id, "values": emb, "metadata": _vector_metadata(d)}
            for d, emb in items
        ]
        # Pinecone recommends batches of <= 100.
        for start in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[start : start + 100])
        return len(vectors)

    # ── reads ──────────────────────────────────────────────────────────────
    def query(
        self, embedding: list[float], top_k: int, filters: SearchFilters
    ) -> list[Match]:
        if self.is_mock:
            return self._mem_query(embedding, top_k, filters)

        result = self._index.query(
            vector=embedding,
            top_k=top_k,
            filter=_build_pinecone_filter(filters),
            include_metadata=False,
        )
        return [(m["id"], float(m["score"])) for m in result["matches"]]

    def count(self) -> int:
        if self.is_mock:
            return len(self._mem)
        try:
            stats = self._index.describe_index_stats()
            return int(stats.get("total_vector_count", 0))
        except Exception:  # pragma: no cover
            return 0

    # ── in-memory fallback ─────────────────────────────────────────────────
    def _mem_query(
        self, embedding: list[float], top_k: int, filters: SearchFilters
    ) -> list[Match]:
        q = np.asarray(embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q) or 1.0
        scored: list[Match] = []
        for _id, (vec, meta) in self._mem.items():
            if not self._passes_filter(meta, filters):
                continue
            cos = float(np.dot(q, vec) / (q_norm * (np.linalg.norm(vec) or 1.0)))
            # Return the RAW cosine (clamped to [0, 1]) to match Pinecone's score
            # exactly — so the displayed match % is consistent and honest whether
            # running on the in-memory store or real Pinecone. Unrelated images
            # then read ~0.7, near-identical ones ~0.95, instead of a flat 0.85+.
            scored.append((_id, max(0.0, min(1.0, cos))))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _passes_filter(meta: dict, filters: SearchFilters) -> bool:
        if filters.budget_max is not None and meta["price_min"] > filters.budget_max:
            return False
        if filters.month and filters.month.lower() not in meta["months"]:
            return False
        if filters.style and filters.style.value not in meta["styles"]:
            return False
        return True
