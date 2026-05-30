"""Supabase Postgres wrapper for destination metadata + search analytics.

Why Supabase and not Pinecone metadata? Pinecone's per-vector metadata is capped at
40KB and is slow to scan across all records. Postgres is the right home for rich,
structured destination data and for the ``search_events`` analytics table.

Falls back to an **in-memory dict** (seeded from the bundled sample catalog) when
Supabase is not configured, so the full stack runs locally with no account.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from core.config import Settings
from models.destination import Destination

logger = logging.getLogger(__name__)


class MetadataStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None
        self.is_mock = not settings.supabase_enabled
        self._mem: dict[str, Destination] = {}
        self._events: list[dict] = []
        if not self.is_mock:
            self._connect()

    def _connect(self) -> None:
        from supabase import create_client

        self._client = create_client(
            self.settings.supabase_url, self.settings.supabase_key
        )
        logger.info("Connected to Supabase.")

    # ── seeding (mock mode) ────────────────────────────────────────────────
    def seed(self, destinations: list[Destination]) -> None:
        """Load sample destinations into the in-memory store (mock mode only)."""
        if not self.is_mock:
            return
        for d in destinations:
            self._mem[d.id] = d
        logger.info("Seeded %d sample destinations (mock mode).", len(self._mem))

    # ── reads ──────────────────────────────────────────────────────────────
    def get_by_ids(self, ids: list[str]) -> list[Destination]:
        """Fetch destinations preserving the order of ``ids`` (Pinecone ranking)."""
        if self.is_mock:
            return [self._mem[i] for i in ids if i in self._mem]

        resp = (
            self._client.table("destinations")
            .select("*")
            .in_("id", ids)
            .execute()
        )
        by_id = {row["id"]: _row_to_destination(row) for row in resp.data}
        return [by_id[i] for i in ids if i in by_id]

    def list_active(self) -> list[Destination]:
        if self.is_mock:
            return [d for d in self._mem.values() if d.is_active]

        resp = (
            self._client.table("destinations")
            .select("*")
            .eq("is_active", True)
            .execute()
        )
        return [_row_to_destination(row) for row in resp.data]

    # ── writes ─────────────────────────────────────────────────────────────
    def upsert(self, dest: Destination) -> None:
        if self.is_mock:
            self._mem[dest.id] = dest
            return
        self._client.table("destinations").upsert(
            _destination_to_row(dest)
        ).execute()

    def log_search(self, event: dict) -> None:
        """Write a row to the ``search_events`` analytics table (best-effort)."""
        event.setdefault(
            "created_at", datetime.now(timezone.utc).isoformat()
        )
        if self.is_mock:
            self._events.append(event)
            return
        try:
            self._client.table("search_events").insert(event).execute()
        except Exception as exc:  # pragma: no cover - analytics is best-effort
            logger.warning("Failed to log search event: %s", exc)


def _destination_to_row(d: Destination) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "country": d.country,
        "tagline": d.tagline,
        "description": d.description,
        "images": [str(u) for u in d.images],
        "price_min_inr": d.price_min_inr,
        "price_max_inr": d.price_max_inr,
        "best_months": d.best_months,
        "travel_styles": [s.value for s in d.travel_styles],
        "highlights": d.highlights,
        "is_active": d.is_active,
    }


def _row_to_destination(row: dict) -> Destination:
    return Destination(
        id=row["id"],
        name=row["name"],
        country=row.get("country", ""),
        tagline=row.get("tagline", ""),
        description=row.get("description", ""),
        images=row.get("images", []),
        price_min_inr=row["price_min_inr"],
        price_max_inr=row["price_max_inr"],
        best_months=row.get("best_months", []),
        travel_styles=row.get("travel_styles", []),
        highlights=row.get("highlights", []),
        is_active=row.get("is_active", True),
    )
