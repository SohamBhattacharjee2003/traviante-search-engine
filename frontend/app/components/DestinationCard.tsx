"use client";

import { motion } from "framer-motion";
import type { DestinationResult, SearchFilters } from "@/lib/types";
import { formatMatch, formatPriceRange, shortMonth, titleCase } from "@/lib/format";

interface Props {
  destination: DestinationResult;
  filters: SearchFilters;
  query?: string | null;
  onQuote: (destination: DestinationResult) => void;
}

export default function DestinationCard({ destination, filters, query, onQuote }: Props) {
  const d = destination;
  const image = d.images[0];

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: d.rank * 0.05 }}
      className="group flex flex-col overflow-hidden rounded border border-border bg-surface transition-colors hover:border-accent"
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        {/* Plain img keeps the demo dependency-free; swap for next/image in prod. */}
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={image}
            alt={d.name}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-surface2 text-muted">
            no image
          </div>
        )}

        {/* Rank + match score badges */}
        <div className="absolute left-3 top-3 flex items-center gap-2">
          <span className="rounded-xs bg-bg/80 px-2 py-1 font-display text-[11px] font-bold text-ink backdrop-blur">
            #{d.rank}
          </span>
        </div>
        <div className="absolute right-3 top-3">
          <span className="rounded-xs border border-accent/40 bg-bg/80 px-2 py-1 text-[10px] font-medium text-accent backdrop-blur">
            {formatMatch(d.score)}
          </span>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div>
          <h3 className="font-display text-base font-bold leading-tight text-ink">{d.name}</h3>
          <p className="text-[11px] uppercase tracking-wider text-muted">{d.country}</p>
        </div>

        {d.tagline && (
          <p className="font-serif text-[13px] italic leading-snug text-muted">{d.tagline}</p>
        )}

        {/* Top highlights */}
        {d.highlights.length > 0 && (
          <ul className="space-y-1">
            {d.highlights.slice(0, 2).map((h) => (
              <li key={h} className="flex items-start gap-1.5 text-[11px] text-muted">
                <span className="text-accent">›</span>
                {h}
              </li>
            ))}
          </ul>
        )}

        {/* Price + best months */}
        <div className="mt-auto flex items-end justify-between gap-2 border-t border-border pt-3">
          <div>
            <div className="font-display text-sm font-bold text-accent">
              {formatPriceRange(d.price_min_inr, d.price_max_inr)}
            </div>
            <div className="text-[10px] text-muted">
              Best: {d.best_months.slice(0, 3).map(shortMonth).join(" · ") || "year-round"}
            </div>
          </div>
        </div>

        {d.match_reason && (
          <div className="text-[10px] text-accent3">{d.match_reason}</div>
        )}

        <button
          type="button"
          onClick={() => onQuote(d)}
          className="mt-1 w-full rounded-xs bg-accent py-2.5 font-display text-[12px] font-bold tracking-wide text-bg transition-opacity hover:opacity-90"
        >
          Get Quote →
        </button>
      </div>
    </motion.article>
  );
}

// Build the enquiry URL that closes the loop into Traviante's existing pipeline.
export function buildEnquiryHref(
  d: DestinationResult,
  filters: SearchFilters,
  query?: string | null,
): string {
  const params = new URLSearchParams({
    destination_id: d.id,
    destination_name: d.name,
    source: "visual_search",
    similarity_score: String(d.score),
  });
  if (filters.budget_max != null) params.set("budget_max", String(filters.budget_max));
  if (filters.month) params.set("travel_month", filters.month);
  if (filters.style) params.set("travel_style", filters.style);
  if (query) params.set("search_query", query);
  return `/enquiry?${params.toString()}`;
}
