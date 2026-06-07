"use client";

import { motion } from "framer-motion";
import type { DestinationResult, SearchFilters } from "@/lib/types";
import { formatMatch, formatPriceRange, shortMonth } from "@/lib/format";

interface Props {
  destination: DestinationResult;
  filters: SearchFilters;
  query?: string | null;
  onQuote: (destination: DestinationResult) => void;
  compact?: boolean; // tighter layout for inline chat rendering
  index?: number; // for staggered entrance when rank isn't meaningful
}

export default function DestinationCard({
  destination,
  onQuote,
  compact = false,
  index,
}: Props) {
  const d = destination;
  const image = d.images[0];
  const order = index ?? d.rank - 1;

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, delay: order * 0.05 }}
      className="group flex flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-[0_1px_2px_rgba(20,17,15,0.04)] transition-all hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-[0_8px_24px_rgba(20,17,15,0.08)]"
    >
      <div className={`relative overflow-hidden ${compact ? "aspect-[16/10]" : "aspect-[4/3]"}`}>
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
          <div className="flex h-full items-center justify-center bg-surface2 text-faint">
            no image
          </div>
        )}

        {/* Rank + match score badges */}
        <div className="absolute left-3 top-3 flex items-center gap-2">
          <span className="rounded-full bg-white/85 px-2.5 py-1 font-display text-[11px] font-semibold text-ink backdrop-blur">
            #{d.rank}
          </span>
        </div>
        <div className="absolute right-3 top-3">
          <span className="tabular rounded-full bg-accent/90 px-2.5 py-1 text-[10px] font-semibold text-white backdrop-blur">
            {formatMatch(d.score)}
          </span>
        </div>
      </div>

      <div className={`flex flex-1 flex-col gap-3 ${compact ? "p-4" : "p-5"}`}>
        <div>
          <h3 className="font-display text-[17px] font-semibold leading-tight text-ink">
            {d.name}
          </h3>
          <p className="text-[10px] uppercase tracking-[0.18em] text-faint">{d.country}</p>
        </div>

        {d.tagline && (
          <p className="font-serif text-[13px] italic leading-snug text-muted">{d.tagline}</p>
        )}

        {/* Top highlights */}
        {!compact && d.highlights.length > 0 && (
          <ul className="space-y-1">
            {d.highlights.slice(0, 2).map((h) => (
              <li key={h} className="flex items-start gap-1.5 text-[11.5px] text-muted">
                <span className="text-accent">›</span>
                {h}
              </li>
            ))}
          </ul>
        )}

        {/* Price + best months */}
        <div className="mt-auto flex items-end justify-between gap-2 border-t border-border pt-3">
          <div>
            <div className="tabular font-display text-sm font-semibold text-ink">
              {formatPriceRange(d.price_min_inr, d.price_max_inr)}
            </div>
            <div className="text-[10px] text-faint">
              Best: {d.best_months.slice(0, 3).map(shortMonth).join(" · ") || "year-round"}
            </div>
          </div>
        </div>

        {d.match_reason && <div className="text-[10.5px] text-accent3">{d.match_reason}</div>}

        <button
          type="button"
          onClick={() => onQuote(d)}
          className="mt-1 w-full rounded-lg bg-accent py-2.5 font-display text-[12.5px] font-semibold tracking-wide text-white transition-opacity hover:opacity-90"
        >
          Get a quote →
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
    source: "ai_concierge",
    similarity_score: String(d.score),
  });
  if (filters.budget_max != null) params.set("budget_max", String(filters.budget_max));
  if (filters.month) params.set("travel_month", filters.month);
  if (filters.style) params.set("travel_style", filters.style);
  if (query) params.set("search_query", query);
  return `/enquiry?${params.toString()}`;
}
