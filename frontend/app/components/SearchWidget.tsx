"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { AnimatePresence, motion } from "framer-motion";

export type SearchMode = "text" | "image";

interface Props {
  loading: boolean;
  onTextSearch: (query: string) => void;
  onImageSearch: (file: File) => void;
}

const MAX_BYTES = 5 * 1024 * 1024;

export default function SearchWidget({ loading, onTextSearch, onImageSearch }: Props) {
  const [mode, setMode] = useState<SearchMode>("text");
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[], rejected: unknown[]) => {
    setError(null);
    if (rejected.length > 0) {
      setError("Please drop a JPEG, PNG or WEBP under 5MB.");
      return;
    }
    const f = accepted[0];
    if (!f) return;
    if (f.size > MAX_BYTES) {
      setError("Image exceeds the 5MB limit.");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/jpeg": [], "image/png": [], "image/webp": [] },
    maxFiles: 1,
    multiple: false,
  });

  const clearImage = () => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
  };

  const submitText = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onTextSearch(query.trim());
  };

  const submitImage = () => {
    if (file) onImageSearch(file);
  };

  return (
    <div className="rounded-lg border border-border bg-surface p-2">
      {/* Mode tabs */}
      <div className="mb-2 flex gap-1 rounded-md bg-surface2 p-1">
        <TabButton active={mode === "text"} onClick={() => setMode("text")}>
          💬 Describe it
        </TabButton>
        <TabButton active={mode === "image"} onClick={() => setMode("image")}>
          🖼️ Upload a photo
        </TabButton>
      </div>

      <AnimatePresence mode="wait">
        {mode === "text" ? (
          <motion.form
            key="text"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onSubmit={submitText}
            className="flex gap-2 p-2"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. snowy mountain honeymoon with cosy chalets"
              className="flex-1 rounded-xs border border-border bg-bg px-4 py-3 text-[13px] text-ink outline-none placeholder:text-muted focus:border-accent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="rounded-xs bg-accent px-6 py-3 font-display text-[13px] font-bold text-bg transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              {loading ? "Searching…" : "Search"}
            </button>
          </motion.form>
        ) : (
          <motion.div
            key="image"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="p-2"
          >
            {preview ? (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={preview}
                  alt="upload preview"
                  className="h-28 w-28 rounded-xs object-cover"
                />
                <div className="flex flex-1 flex-col gap-2">
                  <p className="truncate text-[12px] text-muted">{file?.name}</p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={submitImage}
                      disabled={loading}
                      className="rounded-xs bg-accent px-5 py-2.5 font-display text-[13px] font-bold text-bg transition-opacity hover:opacity-90 disabled:opacity-40"
                    >
                      {loading ? "Searching…" : "Find matches"}
                    </button>
                    <button
                      type="button"
                      onClick={clearImage}
                      disabled={loading}
                      className="rounded-xs border border-border px-5 py-2.5 text-[13px] text-muted hover:text-ink"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div
                {...getRootProps()}
                className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xs border border-dashed py-10 text-center transition-colors ${
                  isDragActive ? "border-accent bg-accent/5" : "border-border hover:border-accent/60"
                }`}
              >
                <input {...getInputProps()} />
                <span className="text-2xl">📸</span>
                <p className="text-[13px] text-ink">
                  {isDragActive ? "Drop your photo…" : "Drag a photo here, or click to browse"}
                </p>
                <p className="text-[11px] text-muted">JPEG / PNG / WEBP · max 5MB</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {error && <p className="px-4 pb-2 text-[12px] text-danger">{error}</p>}
    </div>
  );
}

function TabButton({
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
      className={`flex-1 rounded-xs py-2 text-[12px] font-medium transition-colors ${
        active ? "bg-bg text-accent" : "text-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}
