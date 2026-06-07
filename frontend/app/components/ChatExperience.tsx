"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { sendChat, sendChatImage } from "@/lib/api";
import type {
  ChatHistoryItem,
  ChatTurn,
  DestinationResult,
  SearchFilters,
} from "@/lib/types";
import { shortMonth, titleCase } from "@/lib/format";
import DestinationCard, { buildEnquiryHref } from "./DestinationCard";

const MAX_BYTES = 5 * 1024 * 1024;
const GREETING =
  "Hi, I'm **Aria**, your Traviante travel concierge. Tell me about the trip you're dreaming of — a snowy honeymoon, a budget beach escape, a cultural city break — or upload a photo of a place that moves you, and I'll find destinations that match.";
const STARTERS = [
  "Snowy mountain honeymoon under ₹6L",
  "Tropical beach escape in December",
  "Cultural city break with great food",
  "Adventure trip with hiking",
];

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);
}

// Minimal **bold** renderer for the concierge's replies.
function RichText({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? (
          <strong key={i} className="font-semibold text-ink">
            {p.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}

export default function ChatExperience() {
  const sessionRef = useRef<string>();
  if (!sessionRef.current) sessionRef.current = newId();

  const [turns, setTurns] = useState<ChatTurn[]>([
    { id: "greeting", role: "assistant", content: GREETING, suggestions: STARTERS },
  ]);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [input, setInput] = useState("");
  const [pendingImage, setPendingImage] = useState<{ file: File; url: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const threadRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  // dragenter/leave fire for every child; count depth so the overlay only
  // clears when the cursor truly leaves the chat surface.
  const dragDepth = useRef(0);

  // Auto-scroll to the newest turn.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  const history: ChatHistoryItem[] = useMemo(
    () =>
      turns
        .filter((t) => t.id !== "greeting" && !t.pending && !t.error)
        .map((t) => ({ role: t.role, content: t.content, image: Boolean(t.imageUrl) })),
    [turns],
  );

  const activeFilterCount = useMemo(
    () => [filters.budget_max, filters.month, filters.style].filter(Boolean).length,
    [filters],
  );

  const onQuote = useCallback(
    (d: DestinationResult) => {
      window.location.href = buildEnquiryHref(d, filters, null);
    },
    [filters],
  );

  // ── send a text turn ──────────────────────────────────────────────────
  const submitText = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || busy) return;
      setInput("");

      const userTurn: ChatTurn = { id: newId(), role: "user", content: text };
      const pendingId = newId();
      const snapshot = history;
      setTurns((t) => [
        ...t,
        userTurn,
        { id: pendingId, role: "assistant", content: "", pending: true },
      ]);
      setBusy(true);

      try {
        const res = await sendChat(text, snapshot, filters, sessionRef.current);
        setFilters(res.filters ?? {});
        setTurns((t) =>
          t.map((turn) =>
            turn.id === pendingId
              ? {
                  ...turn,
                  pending: false,
                  content: res.reply,
                  results: res.results,
                  suggestions: res.suggestions,
                  usedLlm: res.used_llm,
                }
              : turn,
          ),
        );
      } catch (e) {
        setTurns((t) =>
          t.map((turn) =>
            turn.id === pendingId
              ? { ...turn, pending: false, error: true, content: (e as Error).message }
              : turn,
          ),
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, filters, history],
  );

  // ── send an image turn ────────────────────────────────────────────────
  const submitImage = useCallback(async () => {
    if (!pendingImage || busy) return;
    const { file, url } = pendingImage;
    const caption = input.trim();
    setInput("");
    setPendingImage(null);

    const userTurn: ChatTurn = {
      id: newId(),
      role: "user",
      content: caption || "What does this place feel like?",
      imageUrl: url,
    };
    const pendingId = newId();
    const snapshot = history;
    setTurns((t) => [
      ...t,
      userTurn,
      { id: pendingId, role: "assistant", content: "", pending: true },
    ]);
    setBusy(true);

    try {
      const res = await sendChatImage(file, snapshot, filters, caption, sessionRef.current);
      setFilters(res.filters ?? {});
      setTurns((t) =>
        t.map((turn) =>
          turn.id === pendingId
            ? {
                ...turn,
                pending: false,
                content: res.reply,
                results: res.results,
                suggestions: res.suggestions,
                usedLlm: res.used_llm,
              }
            : turn,
        ),
      );
    } catch (e) {
      setTurns((t) =>
        t.map((turn) =>
          turn.id === pendingId
            ? { ...turn, pending: false, error: true, content: (e as Error).message }
            : turn,
        ),
      );
    } finally {
      setBusy(false);
    }
  }, [pendingImage, busy, input, filters, history]);

  const pickFile = (f: File | undefined) => {
    if (!f) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(f.type)) return;
    if (f.size > MAX_BYTES) return;
    if (pendingImage) URL.revokeObjectURL(pendingImage.url);
    setPendingImage({ file: f, url: URL.createObjectURL(f) });
  };

  // ── drag & drop a photo anywhere over the chat ────────────────────────
  const isFileDrag = (e: React.DragEvent) =>
    Array.from(e.dataTransfer?.types ?? []).includes("Files");

  const onDragEnter = (e: React.DragEvent) => {
    if (!isFileDrag(e)) return;
    dragDepth.current += 1;
    setDragOver(true);
  };
  const onDragOver = (e: React.DragEvent) => {
    if (isFileDrag(e)) e.preventDefault(); // allow the drop
  };
  const onDragLeave = (e: React.DragEvent) => {
    if (!isFileDrag(e)) return;
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDragOver(false);
  };
  const onDrop = (e: React.DragEvent) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    dragDepth.current = 0;
    setDragOver(false);
    pickFile(e.dataTransfer.files?.[0] ?? undefined);
  };

  const onComposerSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pendingImage) void submitImage();
    else void submitText(input);
  };

  return (
    <div
      className="relative flex h-dvh flex-col bg-bg"
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Drag-and-drop overlay */}
      <AnimatePresence>
        {dragOver && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="pointer-events-none absolute inset-0 z-30 flex items-center justify-center bg-bg/85 backdrop-blur-sm"
          >
            <div className="m-4 flex w-full max-w-lg flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-accent/60 bg-accent-soft/60 px-8 py-14 text-center">
              <div className="grid h-14 w-14 place-items-center rounded-full bg-accent/10 text-accent">
                <CameraIcon />
              </div>
              <p className="font-display text-lg font-semibold text-ink">Drop your photo</p>
              <p className="text-[12.5px] text-muted">
                I&apos;ll find destinations that match its vibe · JPEG / PNG / WEBP, up to 5MB
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="border-b border-border bg-bg/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-3.5">
          <Link href="/" className="font-display text-[19px] font-semibold tracking-tight text-ink">
            Traviante<span className="text-accent">.</span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 text-[11px] text-muted sm:flex">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
              AI Concierge
            </span>
            <FilterSummary filters={filters} count={activeFilterCount} onClear={() => setFilters({})} />
          </div>
        </div>
      </header>

      {/* Thread */}
      <div ref={threadRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-5 py-8">
          {turns.map((turn) =>
            turn.role === "assistant" ? (
              <AssistantTurn
                key={turn.id}
                turn={turn}
                filters={filters}
                onQuote={onQuote}
                onSuggestion={(s) => void submitText(s)}
                disabled={busy}
              />
            ) : (
              <UserTurn key={turn.id} turn={turn} />
            ),
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Composer */}
      <div className="border-t border-border bg-bg">
        <form onSubmit={onComposerSubmit} className="mx-auto max-w-3xl px-5 py-4">
          {pendingImage && (
            <div className="mb-2 flex items-center gap-3 rounded-lg border border-border bg-surface p-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={pendingImage.url} alt="upload preview" className="h-12 w-12 rounded-md object-cover" />
              <span className="flex-1 truncate text-[12px] text-muted">
                {pendingImage.file.name} · add a note or just send
              </span>
              <button
                type="button"
                onClick={() => {
                  URL.revokeObjectURL(pendingImage.url);
                  setPendingImage(null);
                }}
                className="rounded-md px-2 py-1 text-[12px] text-faint hover:text-ink"
              >
                Remove
              </button>
            </div>
          )}

          <div className="flex items-end gap-2 rounded-2xl border border-border bg-surface p-2 shadow-[0_1px_2px_rgba(20,17,15,0.04)] focus-within:border-accent/50">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0] ?? undefined)}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Upload a photo of a place you love"
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-muted transition-colors hover:bg-surface2 hover:text-accent"
            >
              <CameraIcon />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  onComposerSubmit(e);
                }
              }}
              rows={1}
              placeholder={pendingImage ? "Add a note about your photo…" : "Describe your dream trip…"}
              className="max-h-32 flex-1 resize-none bg-transparent px-1 py-2.5 text-[14px] text-ink outline-none placeholder:text-faint"
            />

            <button
              type="submit"
              disabled={busy || (!input.trim() && !pendingImage)}
              className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-accent text-white transition-opacity hover:opacity-90 disabled:opacity-30"
              title="Send"
            >
              {busy ? <Spinner /> : <SendIcon />}
            </button>
          </div>
          <p className="mt-2 text-center text-[10.5px] text-faint">
            Traviante AI matches your words & photos to destinations with CLIP + an LLM concierge.
          </p>
        </form>
      </div>
    </div>
  );
}

// ── turns ─────────────────────────────────────────────────────────────────
function AssistantTurn({
  turn,
  filters,
  onQuote,
  onSuggestion,
  disabled,
}: {
  turn: ChatTurn;
  filters: SearchFilters;
  onQuote: (d: DestinationResult) => void;
  onSuggestion: (s: string) => void;
  disabled: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex gap-3"
    >
      <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent/10 font-display text-[13px] font-semibold text-accent">
        A
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        {turn.pending ? (
          <TypingBubble />
        ) : (
          <div
            className={`text-[14px] leading-relaxed ${
              turn.error ? "text-danger" : "text-ink"
            }`}
          >
            <RichText text={turn.content} />
          </div>
        )}

        {turn.results && turn.results.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {turn.results.map((d, i) => (
              <DestinationCard
                key={d.id}
                destination={d}
                filters={filters}
                onQuote={onQuote}
                compact
                index={i}
              />
            ))}
          </div>
        )}

        {turn.suggestions && turn.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {turn.suggestions.map((s) => (
              <button
                key={s}
                type="button"
                disabled={disabled}
                onClick={() => onSuggestion(s)}
                className="rounded-full border border-border bg-surface px-3.5 py-1.5 text-[12px] text-muted transition-colors hover:border-accent/50 hover:text-accent disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function UserTurn({ turn }: { turn: ChatTurn }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="flex flex-col items-end gap-2"
    >
      {turn.imageUrl && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={turn.imageUrl}
          alt="your upload"
          className="max-h-52 rounded-2xl border border-border object-cover"
        />
      )}
      <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-ink px-4 py-2.5 text-[14px] leading-relaxed text-bg">
        {turn.content}
      </div>
    </motion.div>
  );
}

function TypingBubble() {
  return (
    <div className="flex w-fit items-center gap-1.5 rounded-2xl rounded-bl-sm bg-surface2 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="typing-dot h-1.5 w-1.5 rounded-full bg-muted"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

function FilterSummary({
  filters,
  count,
  onClear,
}: {
  filters: SearchFilters;
  count: number;
  onClear: () => void;
}) {
  if (count === 0) return null;
  const chips = [
    filters.style ? titleCase(filters.style) : null,
    filters.month ? shortMonth(filters.month) : null,
    filters.budget_max ? `≤ ₹${Math.round(filters.budget_max / 100000)}L` : null,
  ].filter(Boolean) as string[];

  return (
    <div className="flex items-center gap-1.5">
      {chips.map((c) => (
        <span
          key={c}
          className="rounded-full border border-accent/30 bg-accent-soft px-2.5 py-1 text-[10.5px] font-medium text-accent"
        >
          {c}
        </span>
      ))}
      <button
        type="button"
        onClick={onClear}
        className="text-[10.5px] text-faint hover:text-ink"
        title="Clear preferences"
      >
        ✕
      </button>
    </div>
  );
}

// ── icons ─────────────────────────────────────────────────────────────────
function CameraIcon() {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 4l1.5 2h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3l1.5-2z" />
      <circle cx="12" cy="12.5" r="3.2" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 2L11 13" />
      <path d="M22 2l-7 20-4-9-9-4 20-7z" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" className="animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" opacity="0.25" />
      <path d="M21 12a9 9 0 0 0-9-9" strokeLinecap="round" />
    </svg>
  );
}
