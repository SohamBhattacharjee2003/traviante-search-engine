// Client-side API helpers. These call the Next.js proxy routes (/api/search/*),
// NOT the backend directly — the backend URL and key stay server-side.

import type { SearchFilters, SearchResponse } from "./types";

function filtersToForm(form: FormData, filters: SearchFilters): void {
  if (filters.budget_max != null) form.append("budget_max", String(filters.budget_max));
  if (filters.month) form.append("month", filters.month);
  if (filters.style) form.append("style", filters.style);
  if (filters.group_size != null) form.append("group_size", String(filters.group_size));
}

export async function searchByImage(
  file: File,
  filters: SearchFilters,
  sessionId?: string,
): Promise<SearchResponse> {
  const form = new FormData();
  form.append("file", file);
  filtersToForm(form, filters);
  if (sessionId) form.append("session_id", sessionId);

  const res = await fetch("/api/search/image", { method: "POST", body: form });
  if (!res.ok) throw new Error((await safeError(res)) ?? "Image search failed");
  return res.json();
}

export async function searchByText(
  query: string,
  filters: SearchFilters,
  sessionId?: string,
): Promise<SearchResponse> {
  const res = await fetch("/api/search/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, ...filters, session_id: sessionId }),
  });
  if (!res.ok) throw new Error((await safeError(res)) ?? "Text search failed");
  return res.json();
}

async function safeError(res: Response): Promise<string | null> {
  try {
    const data = await res.json();
    return typeof data?.detail === "string" ? data.detail : data?.error ?? null;
  } catch {
    return null;
  }
}
