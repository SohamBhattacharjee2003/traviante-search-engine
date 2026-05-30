// Server-side proxy for image search.
// Forwards the multipart upload to the FastAPI backend, keeping BACKEND_URL and
// BACKEND_API_KEY secret from the browser.

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const BACKEND_API_KEY = process.env.BACKEND_API_KEY ?? "dev-frontend-key";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const upstream = await fetch(`${BACKEND_URL}/v1/search/image`, {
      method: "POST",
      headers: { "x-frontend-key": BACKEND_API_KEY },
      body: formData,
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
