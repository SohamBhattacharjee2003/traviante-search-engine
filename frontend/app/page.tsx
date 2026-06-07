import Link from "next/link";

// Landing page — a quiet, editorial hero that funnels into the AI concierge chat.
export default function Home() {
  return (
    <main className="relative mx-auto flex min-h-dvh max-w-5xl flex-col items-center justify-center px-6 text-center">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(47,110,79,0.07),transparent_70%)]" />

      <span className="mb-7 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3.5 py-1.5 text-[11px] font-medium tracking-wide text-muted">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
        Traviante · AI Travel Concierge
      </span>

      <h1 className="font-display text-[40px] font-semibold leading-[1.05] tracking-tight text-ink sm:text-6xl">
        Find your trip by
        <br />
        <span className="text-accent">conversation</span>.
      </h1>

      <p className="mt-6 max-w-xl font-serif text-lg italic leading-relaxed text-muted">
        Chat with Aria, our AI concierge. Describe the journey you&apos;re dreaming of — or
        upload a photo of a place that moves you — and discover premium destinations matched
        to your vibe.
      </p>

      <Link
        href="/search"
        className="mt-9 rounded-full bg-accent px-8 py-3.5 font-display text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        Start the conversation →
      </Link>

      <div className="mt-16 grid w-full max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { icon: "💬", label: "Natural conversation" },
          { icon: "🖼️", label: "Photo matching" },
          { icon: "🧠", label: "CLIP + LLM" },
          { icon: "⚡", label: "Instant matches" },
        ].map((f) => (
          <div
            key={f.label}
            className="rounded-xl border border-border bg-surface px-4 py-4 text-center"
          >
            <div className="text-xl">{f.icon}</div>
            <div className="mt-1.5 text-[11.5px] text-muted">{f.label}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
