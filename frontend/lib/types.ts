// TypeScript interfaces mirroring the backend Pydantic models
// (backend/models/destination.py). Keep these in sync to avoid runtime drift.

export type TravelStyle =
  | "honeymoon"
  | "adventure"
  | "family"
  | "cultural"
  | "beach"
  | "luxury";

export type SearchType = "image" | "text";

export interface Destination {
  id: string;
  name: string;
  country: string;
  tagline: string;
  description: string;
  images: string[];
  price_min_inr: number;
  price_max_inr: number;
  best_months: string[];
  travel_styles: TravelStyle[];
  highlights: string[];
  is_active: boolean;
}

export interface DestinationResult extends Destination {
  score: number; // cosine similarity 0..1
  rank: number; // 1-based
  match_reason: string | null;
}

export interface SearchFilters {
  budget_max?: number | null;
  month?: string | null;
  style?: TravelStyle | null;
  group_size?: number | null;
}

export interface SearchResponse {
  results: DestinationResult[];
  total: number;
  query_time_ms: number;
  search_type: SearchType;
  query_text?: string | null;
  filters?: SearchFilters | null;
  mock_mode: boolean;
}

// ── Conversational concierge ──────────────────────────────────────────
export type ChatRole = "user" | "assistant";

/** A turn sent up to the backend as conversation history. */
export interface ChatHistoryItem {
  role: ChatRole;
  content: string;
  image?: boolean;
}

/** The backend's reply: prose + any destinations the agent surfaced. */
export interface ChatResponse {
  reply: string;
  results: DestinationResult[];
  filters: SearchFilters;
  suggestions: string[];
  used_llm: boolean;
  mock_mode: boolean;
  query_time_ms: number;
}

/** A message rendered in the chat thread (UI-side, richer than history). */
export interface ChatTurn {
  id: string;
  role: ChatRole;
  content: string;
  imageUrl?: string; // local object URL for an uploaded photo
  results?: DestinationResult[];
  suggestions?: string[];
  usedLlm?: boolean;
  pending?: boolean; // assistant turn still streaming/awaiting
  error?: boolean;
}

export const TRAVEL_STYLES: TravelStyle[] = [
  "honeymoon",
  "adventure",
  "family",
  "cultural",
  "beach",
  "luxury",
];

export const MONTHS = [
  "january",
  "february",
  "march",
  "april",
  "may",
  "june",
  "july",
  "august",
  "september",
  "october",
  "november",
  "december",
];

// Budget tiers (in INR) shown as filter chips.
export const BUDGET_TIERS: { label: string; value: number }[] = [
  { label: "Under ₹1L", value: 100000 },
  { label: "Under ₹3L", value: 300000 },
  { label: "Under ₹5L", value: 500000 },
  { label: "Under ₹10L", value: 1000000 },
];
