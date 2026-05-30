// Server-side proxy for text search.
// Forwards the JSON query to the FastAPI backend, keeping BACKEND_URL secret.

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const BACKEND_API_KEY = process.env.BACKEND_API_KEY ?? "dev-frontend-key";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const sessionId = body.session_id as string | undefined;

    // Strip session_id from the body (backend takes it as a query param) and
    // drop null/empty filters so Pydantic validation stays happy.
    const { session_id, ...rest } = body;
    const payload = Object.fromEntries(
      Object.entries(rest).filter(([, v]) => v !== null && v !== undefined && v !== ""),
    );

    const url = new URL(`${BACKEND_URL}/v1/search/text`);
    if (sessionId) url.searchParams.set("session_id", sessionId);

    const upstream = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-frontend-key": BACKEND_API_KEY,
      },
      body: JSON.stringify(payload),
    });

    const data = await upstream.json().catch(() => ({ detail: "Bad backend response" }));
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    return NextResponse.json(
      { detail: `Backend unreachable: ${(err as Error).message}` },
      { status: 502 },
    );
  }
}
