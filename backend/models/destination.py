"""Pydantic v2 data models — the contract shared across every layer.

These mirror the TypeScript interfaces in ``frontend/lib/types.ts`` and the
columns in ``db/schema.sql``. FastAPI generates the OpenAPI docs from them and
validates all input / output automatically.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class TravelStyle(str, Enum):
    honeymoon = "honeymoon"
    adventure = "adventure"
    family = "family"
    cultural = "cultural"
    beach = "beach"
    luxury = "luxury"


class SearchType(str, Enum):
    image = "image"
    text = "text"


class Destination(BaseModel):
    """A full destination record (stored in Supabase)."""

    id: str = Field(..., description="Unique slug, e.g. 'bali-ubud'")
    name: str = Field(..., description="Display name, e.g. 'Ubud, Bali'")
    country: str
    tagline: str = Field(default="", description="One-line hook")
    description: str = Field(default="", description="Rich text for text embedding")
    images: list[HttpUrl] = Field(default_factory=list, min_length=0)
    price_min_inr: int = Field(..., ge=0)
    price_max_inr: int = Field(..., ge=0)
    best_months: list[str] = Field(default_factory=list)
    travel_styles: list[TravelStyle] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    is_active: bool = True

    @property
    def primary_image(self) -> str | None:
        return str(self.images[0]) if self.images else None


class DestinationResult(Destination):
    """A destination returned from search — adds the similarity score + rank."""

    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity")
    rank: int = Field(..., ge=1, description="1-based rank in the result set")
    match_reason: str | None = Field(
        default=None, description="Human-readable explanation of the match"
    )


class SearchFilters(BaseModel):
    """Metadata filters applied to the Pinecone query before ranking."""

    budget_max: int | None = Field(default=None, ge=0)
    month: str | None = None
    style: TravelStyle | None = None
    group_size: int | None = Field(default=None, ge=1)

    def is_empty(self) -> bool:
        return not any(
            (self.budget_max, self.month, self.style, self.group_size)
        )


class SearchResponse(BaseModel):
    results: list[DestinationResult]
    total: int
    query_time_ms: int
    search_type: SearchType
    query_text: str | None = None
    filters: SearchFilters | None = None
    mock_mode: bool = False


class TextSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    budget_max: int | None = Field(default=None, ge=0)
    month: str | None = None
    style: TravelStyle | None = None
    group_size: int | None = Field(default=None, ge=1)

    def to_filters(self) -> SearchFilters:
        return SearchFilters(
            budget_max=self.budget_max,
            month=self.month,
            style=self.style,
            group_size=self.group_size,
        )


class DestinationCreate(Destination):
    """Payload for the admin create/upsert endpoint."""


class HealthResponse(BaseModel):
    status: str
    environment: str
    clip_model: str
    clip_device: str
    pinecone_enabled: bool
    supabase_enabled: bool
    mock_mode: bool
    indexed_vectors: int | None = None
