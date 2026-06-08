import Link from "next/link";
import ThemeSwitcher from "@/app/components/ThemeSwitcher";

// Landing page — a futuristic, professional hero that funnels into the AI concierge.
export default function Home() {
  return (
    <main className="relative flex min-h-dvh flex-col overflow-hidden bg-bg">
      {/* Ambient futuristic backdrop: tech grid + drifting neon orbs + glow */}
      <div className="grid-bg pointer-events-none absolute inset-0 opacity-70" />
      <div className="glow pointer-events-none absolute inset-x-0 top-0 h-[65vh]" />
      <div className="drift pointer-events-none absolute -left-28 top-32 h-80 w-80 rounded-full bg-accent/20 blur-[120px]" />
      <div
        className="drift pointer-events-none absolute -right-24 top-16 h-72 w-72 rounded-full bg-accent2/20 blur-[120px]"
        style={{ animationDelay: "3s" }}
      />
      <div
        className="drift pointer-events-none absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-accent3/15 blur-[120px]"
        style={{ animationDelay: "6s" }}
      />

      {/* Top bar */}
      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <span className="font-display text-[20px] font-semibold tracking-tight text-ink">
          Traviante<span className="text-accent">.</span>
        </span>
        <ThemeSwitcher />
      </header>

      {/* Hero */}
      <div className="relative z-10 mx-auto flex max-w-5xl flex-1 flex-col items-center justify-center px-6 pb-24 text-center">
        <span className="rise mb-7 inline-flex items-center gap-2 rounded-full border border-border bg-surface/50 px-3.5 py-1.5 text-[11px] font-medium tracking-wide text-muted backdrop-blur">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-60" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
          </span>
          AI Travel Concierge · CLIP + LLM
        </span>

        <h1
          className="rise font-display text-[44px] font-semibold leading-[1.02] tracking-tight text-ink sm:text-7xl"
          style={{ animationDelay: "0.05s" }}
        >
          Find your trip by
          <br />
          <span className="text-gradient italic">conversation</span>.
        </h1>

        <p
          className="rise mt-6 max-w-xl text-[17px] leading-relaxed text-muted sm:text-lg"
          style={{ animationDelay: "0.12s" }}
        >
          Chat with <span className="text-ink">Aria</span>, our AI concierge. Describe the
          journey you&apos;re dreaming of — or upload a photo of a place that moves you — and
          discover premium destinations matched to your vibe.
        </p>

        <div
          className="rise mt-9 flex flex-col items-center gap-3 sm:flex-row"
          style={{ animationDelay: "0.2s" }}
        >
          <Link
            href="/search"
            className="group inline-flex items-center gap-2 rounded-full bg-accent px-8 py-4 font-display text-sm font-semibold text-white shadow-glow transition-all hover:-translate-y-0.5"
          >
            Start the conversation
            <span className="transition-transform group-hover:translate-x-0.5">→</span>
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/50 px-6 py-4 font-display text-sm font-semibold text-ink backdrop-blur transition-colors hover:border-accent/50"
          >
            🖼️ Upload a photo
          </Link>
        </div>

        <div
          className="rise mt-16 grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4"
          style={{ animationDelay: "0.28s" }}
        >
          {[
            { icon: "💬", label: "Natural conversation" },
            { icon: "🖼️", label: "Photo matching" },
            { icon: "🧠", label: "CLIP + LLM engine" },
            { icon: "⚡", label: "Instant matches" },
          ].map((f) => (
            <div
              key={f.label}
              className="glass rounded-2xl px-4 py-5 text-center shadow-card transition-all hover:-translate-y-1 hover:border-accent/40 hover:shadow-card-hover"
            >
              <div className="text-2xl">{f.icon}</div>
              <div className="mt-2 text-[11.5px] text-muted">{f.label}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
