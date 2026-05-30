"use client";

import { motion } from "framer-motion";
import type { DestinationResult, SearchFilters } from "@/lib/types";
import DestinationCard from "./DestinationCard";

interface Props {
  results: DestinationResult[];
  filters: SearchFilters;
  query?: string | null;
  loading: boolean;
  error: string | null;
  hasSearched: boolean;
  queryTimeMs?: number;
  mockMode?: boolean;
  onQuote: (destination: DestinationResult) => void;
  onClearFilters: () => void;
}

export default function SearchResults({
  results,
  filters,
  query,
  loading,
  error,
  hasSearched,
  queryTimeMs,
  mockMode,
  onQuote,
  onClearFilters,
}: Props) {
  if (loading) return <SkeletonGrid />;

  if (error) {
    return (
      <div className="rounded border border-danger/40 bg-danger/5 p-6 text-center">
        <p className="font-display text-sm font-bold text-danger">Search failed</p>
        <p className="mt-1 text-[12px] text-muted">{error}</p>
      </div>
    );
  }

  if (!hasSearched) {
    return (
      <div className="rounded border border-border bg-surface p-10 text-center">
        <p className="font-serif text-[15px] italic text-muted">
          Upload a photo or describe your dream trip to see matching destinations.
        </p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="rounded border border-border bg-surface p-10 text-center">
        <p className="font-display text-sm font-bold text-ink">No destinations matched</p>
        <p className="mt-1 text-[12px] text-muted">
          Try removing a filter or describing the vibe differently.
        </p>
        <button
          type="button"
          onClick={onClearFilters}
          className="mt-4 rounded-xs border border-accent/40 px-4 py-2 text-[12px] text-accent hover:bg-accent/10"
        >
          Clear filters
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between text-[11px] text-muted">
        <span>
          {results.length} destination{results.length > 1 ? "s" : ""}
          {typeof queryTimeMs === "number" && ` · ${queryTimeMs}ms`}
        </span>
        {mockMode && (
          <span className="rounded-xs border border-warn/40 bg-warn/5 px-2 py-0.5 text-warn">
            mock mode — sample data
          </span>
        )}
      </div>

      <motion.div
        layout
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {results.map((d) => (
          <DestinationCard
            key={d.id}
            destination={d}
            filters={filters}
            query={query}
            onQuote={onQuote}
          />
        ))}
      </motion.div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="overflow-hidden rounded border border-border bg-surface">
          <div className="skeleton aspect-[4/3]" />
          <div className="space-y-3 p-5">
            <div className="skeleton h-4 w-2/3 rounded-xs" />
            <div className="skeleton h-3 w-1/3 rounded-xs" />
            <div className="skeleton h-3 w-full rounded-xs" />
            <div className="skeleton h-9 w-full rounded-xs" />
          </div>
        </div>
      ))}
    </div>
  );
}
