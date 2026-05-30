"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { searchByImage, searchByText } from "@/lib/api";
import type { DestinationResult, SearchFilters } from "@/lib/types";
import SearchWidget from "@/app/components/SearchWidget";
import FilterPanel from "@/app/components/FilterPanel";
import SearchResults from "@/app/components/SearchResults";
import { buildEnquiryHref } from "@/app/components/DestinationCard";

// A stable per-tab session id so search analytics can group a user's events.
function useSessionId(): string {
  const ref = useRef<string>();
  if (!ref.current) {
    ref.current =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : Math.random().toString(36).slice(2);
  }
  return ref.current;
}

export default function SearchPage() {
  const sessionId = useSessionId();
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<DestinationResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [queryTimeMs, setQueryTimeMs] = useState<number | undefined>();
  const [mockMode, setMockMode] = useState(false);
  const [lastQuery, setLastQuery] = useState<string | null>(null);

  const activeFilterCount = useMemo(
    () => [filters.budget_max, filters.month, filters.style].filter(Boolean).length,
    [filters],
  );

  const runTextSearch = useCallback(
    async (query: string) => {
      setLoading(true);
      setError(null);
      setHasSearched(true);
      setLastQuery(query);
      try {
        const res = await searchByText(query, filters, sessionId);
        setResults(res.results);
        setQueryTimeMs(res.query_time_ms);
        setMockMode(res.mock_mode);
      } catch (e) {
        setError((e as Error).message);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [filters, sessionId],
  );

  const runImageSearch = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);
      setHasSearched(true);
      setLastQuery(null);
      try {
        const res = await searchByImage(file, filters, sessionId);
        setResults(res.results);
        setQueryTimeMs(res.query_time_ms);
        setMockMode(res.mock_mode);
      } catch (e) {
        setError((e as Error).message);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [filters, sessionId],
  );

  const handleQuote = useCallback(
    (destination: DestinationResult) => {
      // Closes the loop into Traviante's enquiry pipeline with attribution params.
      window.location.href = buildEnquiryHref(destination, filters, lastQuery);
    },
    [filters, lastQuery],
  );

  return (
    <main className="mx-auto max-w-6xl px-5 py-10">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <Link href="/" className="font-display text-lg font-extrabold tracking-tight">
          Traviante<span className="text-accent">.</span>
        </Link>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
          Visual Destination Search
        </span>
      </header>

      <h1 className="mb-1 font-display text-2xl font-bold sm:text-3xl">
        Find trips by <span className="text-accent">vibe</span>
      </h1>
      <p className="mb-6 font-serif text-[15px] italic text-muted">
        Upload a photo or describe the trip you&apos;re dreaming of.
      </p>

      <div className="mb-6">
        <SearchWidget
          loading={loading}
          onTextSearch={runTextSearch}
          onImageSearch={runImageSearch}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
              Filters
            </h2>
            {activeFilterCount > 0 && (
              <button
                type="button"
                onClick={() => setFilters({})}
                className="text-[10px] text-accent hover:underline"
              >
                Clear ({activeFilterCount})
              </button>
            )}
          </div>
          <FilterPanel filters={filters} onChange={setFilters} />
        </aside>

        <section>
          <SearchResults
            results={results}
            filters={filters}
            query={lastQuery}
            loading={loading}
            error={error}
            hasSearched={hasSearched}
            queryTimeMs={queryTimeMs}
            mockMode={mockMode}
            onQuote={handleQuote}
            onClearFilters={() => setFilters({})}
          />
        </section>
      </div>
    </main>
  );
}
