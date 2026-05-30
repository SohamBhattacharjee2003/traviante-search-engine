# Traviante — AI Visual Destination Search

A multimodal search engine that lets customers find Traviante travel destinations by
**uploading a photo** _or_ **typing a natural-language query** — returning ranked
destination cards in under two seconds.

It is powered by [OpenAI CLIP](https://github.com/openai/CLIP), which maps **images and
text into the same 512-dimensional embedding space**. A photo of a snowy Swiss village
and the text _"snowy mountain honeymoon"_ land near each other in vector space, enabling
true multimodal search with a single model and no fine-tuning.

```
            ┌──────────────┐      ┌──────────────┐      ┌─────────────────────┐
  user ───▶ │  Next.js 14  │ ───▶ │   FastAPI    │ ───▶ │ CLIP · Pinecone ·   │
  photo/    │  (Vercel)    │ HTTPS│ (HF Spaces)  │ SDK  │ Supabase · Cloudinary│
  text      └──────────────┘      └──────────────┘      └─────────────────────┘
       proxy route hides backend     CLIP encode 512-d     vector + metadata search
```

## Architecture (3 layers)

| Layer | Tech | Responsibility |
|-------|------|----------------|
| **L1 — Presentation** | Next.js 14 (App Router), React 18, Tailwind, Framer Motion | Search widget, filters, result cards. Deployed on Vercel. |
| **L2 — API** | FastAPI, Pydantic v2, Uvicorn | Stateless REST. Validation, CLIP inference, Pinecone queries, Supabase fetch. |
| **L3 — ML & Data** | CLIP ViT-B/32, Pinecone Serverless, Supabase Postgres, Cloudinary | Embeddings, vector search, metadata, image CDN. |

The frontend never talks to the backend directly — Next.js **Route Handlers** proxy
requests server-side so the backend URL and API key stay secret.

## Repository layout

```
traviante-visual-search/
├── backend/                  # FastAPI + CLIP ML service
│   ├── main.py               # App entry — loads CLIP once on startup
│   ├── api/                  # search, destinations, health routers
│   ├── core/                 # clip_encoder, vector_store, metadata_store, config
│   ├── models/               # Pydantic v2 contracts
│   ├── scripts/              # one-time offline indexing pipeline
│   ├── db/schema.sql         # Supabase Postgres schema + analytics views
│   ├── Dockerfile            # HuggingFace Spaces / Railway deploy
│   └── requirements.txt
└── frontend/                 # Next.js 14 app
    ├── app/                  # pages, components, API proxy routes
    └── lib/                  # types (mirror Pydantic) + API client
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Pinecone / Supabase keys
uvicorn main:app --reload     # http://localhost:8000/docs
```

> The backend runs in **mock mode** automatically when `PINECONE_API_KEY` /
> `SUPABASE_URL` are not set — it serves bundled sample destinations so you can develop
> the full stack with zero external accounts. See `core/config.py`.

### 2. Index destinations (once you have real keys)

```bash
# 1. Apply the schema to your Supabase project (db/schema.sql)
# 2. Edit backend/scripts/destinations_data.py with your catalog
python -m scripts.index_destinations
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # point BACKEND_URL at the API
npm run dev                         # http://localhost:3000/search
```

## Cost at MVP scale (all free tier except backend host)

| Service | Cost/mo | Notes |
|---------|---------|-------|
| Vercel (Next.js) | ₹0 | Free hobby tier |
| HuggingFace Spaces (FastAPI) | ₹0 | Free Docker, 16GB / 2 vCPU |
| Pinecone Serverless | ₹0 | Free up to 1M vectors |
| Supabase | ₹0 | Free up to 500MB |
| Cloudinary | ₹0 | 25GB free |
| **Total** | **~₹0–420/mo** | Railway Hobby ($5) if you move off HF Spaces |

## Documentation

- [`backend/README.md`](backend/README.md) — backend deep-dive (endpoints, mock mode, deploy)
- [`frontend/README.md`](frontend/README.md) — frontend deep-dive (Tailwind v4, proxy routes)

This implementation follows the original engineering blueprint and architecture diagram
that specified the 3-layer design (Next.js · FastAPI · CLIP/Pinecone/Supabase).
