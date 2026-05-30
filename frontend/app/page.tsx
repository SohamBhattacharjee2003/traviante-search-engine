import Link from "next/link";

// Landing page — a short hero that funnels into the search experience.
export default function Home() {
  return (
    <main className="relative mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 text-center">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,rgba(0,212,170,0.08),transparent_70%)]" />

      <span className="mb-6 inline-block rounded-xs border border-accent/30 bg-accent/10 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-accent">
        Traviante · AI Visual Search
      </span>

      <h1 className="font-display text-4xl font-extrabold leading-tight tracking-tight text-ink sm:text-6xl">
        Find trips by <span className="text-accent">vibe</span>
      </h1>

      <p className="mt-5 max-w-xl font-serif text-lg italic text-muted">
        Upload a photo of a place that moves you — or just describe it — and we&apos;ll
        surface the Traviante destinations that match, in seconds.
      </p>

      <Link
        href="/search"
        className="mt-9 rounded-xs bg-accent px-8 py-3.5 font-display text-sm font-bold text-bg transition-opacity hover:opacity-90"
      >
        Start searching →
      </Link>

      <div className="mt-14 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 font-mono text-[11px] text-muted">
        <span>🖼️ Image search</span>
        <span>💬 Natural language</span>
        <span>⚡ &lt;2s results</span>
        <span>🧠 Powered by CLIP</span>
      </div>
    </main>
  );
}
