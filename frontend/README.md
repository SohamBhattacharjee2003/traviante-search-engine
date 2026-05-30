# Traviante Frontend — Next.js 14

The customer-facing search experience. Drag-drop image upload or natural-language
query → ranked destination cards with a "Get Quote" CTA that flows into Traviante's
enquiry pipeline.

## Stack

- **Next.js 14** (App Router) · React 18 · TypeScript
- **Tailwind CSS v4** (CSS-first config — no `tailwind.config.*`)
- **Framer Motion** for card stagger + tab transitions
- **react-dropzone** for image upload

## Tailwind v4 setup

This project uses the **v4 CSS-first** approach (reset from the older v3 config):

- `postcss.config.mjs` → `@tailwindcss/postcss` plugin (Next.js compiles CSS via
  PostCSS; the docs' `@tailwindcss/vite` plugin is for Vite projects only).
- `app/globals.css` → a single `@import "tailwindcss";` plus an `@theme { … }` block
  that defines the design tokens (colors, fonts, radii). There is **no JS config file**.
- `autoprefixer` is built into v4 and no longer a separate dependency.

To add a color, drop a `--color-foo` token in the `@theme` block and use
`bg-foo` / `text-foo` / `border-foo` anywhere.

## Layout

```
frontend/
├── app/
│   ├── layout.tsx                 # root layout + fonts + metadata
│   ├── page.tsx                   # landing hero → /search
│   ├── globals.css                # Tailwind v4 import + @theme tokens
│   ├── search/page.tsx            # stateful search orchestrator
│   ├── components/
│   │   ├── SearchWidget.tsx       # text + image dual-mode input
│   │   ├── FilterPanel.tsx        # budget / month / style chips
│   │   ├── SearchResults.tsx      # grid, skeletons, empty/error states
│   │   └── DestinationCard.tsx    # card + enquiry href builder
│   └── api/search/
│       ├── image/route.ts         # proxy → backend /v1/search/image
│       └── text/route.ts          # proxy → backend /v1/search/text
└── lib/
    ├── types.ts                   # mirrors backend Pydantic models
    ├── format.ts                  # INR / match-score formatting
    └── api.ts                     # client fetch helpers
```

## Run locally

```bash
npm install
cp .env.local.example .env.local   # set BACKEND_URL (default http://localhost:8000)
npm run dev                        # http://localhost:3000  → /search
```

The backend can run in mock mode (no external accounts) — see `../backend/README.md`.

## Why the proxy routes?

The browser never sees the backend URL or key. `app/api/search/*/route.ts` run
server-side, read `BACKEND_URL` / `BACKEND_API_KEY` from the environment, and forward
the request. This prevents direct backend abuse and keeps secrets off the client.

## Deploy (Vercel)

Connect the repo, set the project root to `frontend/`, add `BACKEND_URL` and
`BACKEND_API_KEY` as environment variables, and push. Auto-deploys on every commit.
