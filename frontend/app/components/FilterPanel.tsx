"use client";

import {
  BUDGET_TIERS,
  MONTHS,
  TRAVEL_STYLES,
  type SearchFilters,
  type TravelStyle,
} from "@/lib/types";
import { shortMonth, titleCase } from "@/lib/format";

interface Props {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

// A toggleable filter chip. Clicking an active chip clears it.
function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xs border px-3 py-1 text-[11px] tracking-wide transition-colors ${
        active
          ? "border-accent bg-accent/10 text-accent"
          : "border-border bg-surface2 text-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

export default function FilterPanel({ filters, onChange }: Props) {
  const set = (patch: Partial<SearchFilters>) => onChange({ ...filters, ...patch });

  const toggleBudget = (v: number) =>
    set({ budget_max: filters.budget_max === v ? null : v });
  const toggleMonth = (m: string) =>
    set({ month: filters.month === m ? null : m });
  const toggleStyle = (s: TravelStyle) =>
    set({ style: filters.style === s ? null : s });

  return (
    <div className="space-y-5 rounded border border-border bg-surface p-5">
      <div>
        <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
          Budget
        </h3>
        <div className="flex flex-wrap gap-2">
          {BUDGET_TIERS.map((b) => (
            <Chip
              key={b.value}
              active={filters.budget_max === b.value}
              onClick={() => toggleBudget(b.value)}
            >
              {b.label}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
          Best month
        </h3>
        <div className="flex flex-wrap gap-2">
          {MONTHS.map((m) => (
            <Chip
              key={m}
              active={filters.month === m}
              onClick={() => toggleMonth(m)}
            >
              {shortMonth(m)}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
          Travel style
        </h3>
        <div className="flex flex-wrap gap-2">
          {TRAVEL_STYLES.map((s) => (
            <Chip
              key={s}
              active={filters.style === s}
              onClick={() => toggleStyle(s)}
            >
              {titleCase(s)}
            </Chip>
          ))}
        </div>
      </div>
    </div>
  );
}
