"use client";

import { motion } from "framer-motion";
import type { DestinationResult, SearchFilters } from "@/lib/types";
import { formatPriceRange, shortMonth } from "@/lib/format";

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
  const matchPct = Math.round(d.score * 100);

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: order * 0.06 }}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-card transition-all duration-300 hover:-translate-y-1.5 hover:border-accent/50 hover:shadow-card-hover"
    >
      {/* ── Image with overlaid title ───────────────────────────────────── */}
      <div className={`relative overflow-hidden ${compact ? "aspect-5/4" : "aspect-4/3"}`}>
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={image}
            alt={d.name}
            className="h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.08]"
            loading="lazy"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-surface2 text-faint">
            no image
          </div>
        )}

        {/* Cinematic scrim for legible overlay text */}
        <div className="pointer-events-none absolute inset-0 bg-linear-to-t from-black/80 via-black/15 to-black/25" />

        {/* Rank */}
        <span className="absolute left-3 top-3 grid h-7 w-7 place-items-center rounded-full border border-white/20 bg-black/40 font-display text-[11px] font-semibold text-white backdrop-blur">
          {d.rank}
        </span>

        {/* Match score */}
        <span className="tabular absolute right-3 top-3 inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-black/40 px-2.5 py-1 text-[10.5px] font-semibold text-white backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-accent3" />
          {matchPct}%
        </span>

        {/* Title block overlaid on the photo */}
        <div className="absolute inset-x-0 bottom-0 p-4">
          <h3 className="font-display text-[20px] font-semibold leading-tight text-white drop-shadow-sm">
            {d.name}
          </h3>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.2em] text-white/70">
            {d.country}
          </p>
        </div>

        {/* Match-strength bar hugging the image's bottom edge */}
        <div className="absolute inset-x-0 bottom-0 h-1 bg-black/30">
          <div
            className="h-full bg-linear-to-r from-accent via-accent2 to-accent3"
            style={{ width: `${Math.max(8, matchPct)}%` }}
          />
        </div>
      </div>

      {/* ── Details ─────────────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col gap-3 p-4">
        {d.tagline && (
          <p className="line-clamp-2 font-serif text-[13px] italic leading-snug text-muted">
            {d.tagline}
          </p>
        )}

        {!compact && d.highlights.length > 0 && (
          <ul className="space-y-1">
            {d.highlights.slice(0, 2).map((h) => (
              <li key={h} className="flex items-start gap-1.5 text-[11.5px] text-muted">
                <span className="text-accent3">›</span>
                {h}
              </li>
            ))}
          </ul>
        )}

        <div className="mt-auto flex items-end justify-between gap-2 border-t border-border pt-3">
          <div>
            <div className="tabular text-gradient font-display text-[17px] font-semibold">
              {formatPriceRange(d.price_min_inr, d.price_max_inr)}
            </div>
            <div className="mt-0.5 text-[10px] text-faint">
              Best · {d.best_months.slice(0, 3).map(shortMonth).join(" / ") || "year-round"}
            </div>
          </div>
          {d.match_reason && (
            <span className="rounded-full border border-accent/25 bg-accent-soft px-2.5 py-1 text-[9.5px] font-medium uppercase tracking-wide text-accent">
              {d.match_reason.replace(/^Matches your |^Great for /i, "")}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => onQuote(d)}
          className="group/btn mt-1 inline-flex w-full items-center justify-center gap-1.5 rounded-xl bg-linear-to-r from-accent to-accent2 py-2.5 font-display text-[12.5px] font-semibold tracking-wide text-white transition-all hover:shadow-glow"
        >
          Get a quote
          <span className="transition-transform group-hover/btn:translate-x-0.5">→</span>
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
