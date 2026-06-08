"use client";

import { useEffect, useState } from "react";

export const THEMES = [
  { id: "aurora", label: "Aurora", dot: "#4f8cff", hint: "Deep-space neon" },
  { id: "quantum", label: "Quantum", dot: "#00e0c7", hint: "Carbon mint-teal" },
  { id: "platinum", label: "Platinum", dot: "#4f46e5", hint: "Clean light pro" },
] as const;

export type ThemeId = (typeof THEMES)[number]["id"];

const STORAGE_KEY = "traviante-theme";

/** Compact palette switcher — three swatches; persists choice to localStorage. */
export default function ThemeSwitcher({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<ThemeId>("aurora");

  // Sync from whatever the no-FOUC inline script already applied.
  useEffect(() => {
    const current =
      (document.documentElement.dataset.theme as ThemeId | undefined) ??
      (localStorage.getItem(STORAGE_KEY) as ThemeId | null) ??
      "aurora";
    setTheme(current);
  }, []);

  const apply = (id: ThemeId) => {
    setTheme(id);
    document.documentElement.dataset.theme = id;
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      /* private mode — non-fatal */
    }
  };

  return (
    <div
      className={`flex items-center gap-1 rounded-full border border-border bg-surface/70 p-1 backdrop-blur ${className}`}
      role="radiogroup"
      aria-label="Colour theme"
    >
      {THEMES.map((t) => {
        const active = theme === t.id;
        return (
          <button
            key={t.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => apply(t.id)}
            title={`${t.label} · ${t.hint}`}
            className={`grid h-6 w-6 place-items-center rounded-full transition-all ${
              active ? "ring-2 ring-accent/40" : "opacity-70 hover:opacity-100"
            }`}
          >
            <span
              className="h-3.5 w-3.5 rounded-full ring-1 ring-black/10"
              style={{ background: t.dot }}
            />
            <span className="sr-only">{t.label}</span>
          </button>
        );
      })}
    </div>
  );
}
