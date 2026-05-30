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
