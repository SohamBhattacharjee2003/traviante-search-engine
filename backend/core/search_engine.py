"""Shared ranking pipeline — the single source of truth for how a query
becomes a ranked list of destinations.

Both the REST search endpoints (``api/search.py``) and the conversational
concierge (``core/chat_agent.py``) call into here, so an image search, a text
search and the chatbot's "search_destinations" tool all rank identically.

Two entry points:
    rank_image(embedding, ...)        — pure vector similarity (CLIP image space)
    rank_text(query, embedding, ...)  — lexical ⊕ semantic blend (see _rank_text)
"""
from __future__ import annotations

import re

from core.metadata_store import MetadataStore
from core.vector_store import VectorStore
from models.destination import (
    Destination,
    DestinationResult,
    SearchFilters,
    TravelStyle,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def match_reason(styles: list[TravelStyle], filters: SearchFilters) -> str | None:
    if filters.style and filters.style in styles:
        return f"Matches your {filters.style.value} style"
    if styles:
        return f"Great for {styles[0].value}"
    return None


def dest_passes_filter(dest: Destination, filters: SearchFilters) -> bool:
    if filters.budget_max is not None and dest.price_min_inr > filters.budget_max:
        return False
    if filters.month and filters.month.lower() not in {
        m.lower() for m in dest.best_months
    }:
        return False
    if filters.style and filters.style not in dest.travel_styles:
        return False
    return True


def _lexical_score(query: str, query_tokens: set[str], dest: Destination) -> float:
    """Text-overlap score between a query and a destination's fields.

    An exact name match scores 1.0; a name substring 0.9; otherwise the score is
    the fraction of query tokens found across the destination's text fields, with
    a boost when those tokens land in the name. Returns 0.0 for no overlap.
    """
    name = dest.name.lower()
    if query == name:
        return 1.0
    if query and (query in name or query in dest.country.lower()):
        return 0.9
    if not query_tokens:
        return 0.0

    text = " ".join(
        [
            dest.name,
            dest.country,
            dest.tagline,
            dest.description,
            " ".join(dest.highlights),
            " ".join(s.value for s in dest.travel_styles),
        ]
    ).lower()
    text_tokens = set(_TOKEN_RE.findall(text))
    overlap = query_tokens & text_tokens
    if not overlap:
        return 0.0

    score = len(overlap) / len(query_tokens)
    if query_tokens & set(_TOKEN_RE.findall(name)):
        score = min(1.0, score + 0.3)
    return score


def rank_image(
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
                match_reason=match_reason(dest.travel_styles, filters),
            )
        )
    return results


def rank_text(
    query: str,
    embedding: list[float] | None,
    filters: SearchFilters,
    vector_store: VectorStore,
    metadata_store: MetadataStore,
    top_k: int,
) -> list[DestinationResult]:
    """Rank a text query by blending lexical and semantic (CLIP) similarity.

    For each candidate the final score is ``max(lexical, semantic)``: a typed
    destination name (lexical 1.0) wins outright, while a "vibe" query with no
    keyword overlap rides on the CLIP cosine. ``embedding`` is ``None`` when CLIP
    is mocked — then only the lexical signal counts and irrelevant destinations
    (score 0) are dropped rather than shown with a meaningless match %.
    """
    q = query.lower().strip()
    q_tokens = set(_TOKEN_RE.findall(q))

    candidates = [
        d for d in metadata_store.list_active() if dest_passes_filter(d, filters)
    ]

    semantic: dict[str, float] = {}
    if embedding is not None:
        fetch_k = max(top_k, len(candidates))
        semantic = dict(vector_store.query(embedding, top_k=fetch_k, filters=filters))

    scored: list[tuple[float, Destination]] = []
    for dest in candidates:
        score = max(_lexical_score(q, q_tokens, dest), semantic.get(dest.id, 0.0))
        if score > 0.0:
            scored.append((score, dest))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        DestinationResult(
            **dest.model_dump(),
            score=round(score, 4),
            rank=rank,
            match_reason=match_reason(dest.travel_styles, filters),
        )
        for rank, (score, dest) in enumerate(scored[:top_k], start=1)
    ]
