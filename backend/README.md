# Traviante Backend — FastAPI + CLIP

Stateless REST API that turns an image or a text query into a ranked list of
destinations. CLIP runs inference in-process; Pinecone holds the vectors; Supabase
holds the rich metadata and analytics.

## Layout

```
backend/
├── main.py                 # app entry — loads CLIP once via lifespan
├── api/
│   ├── deps.py             # service accessors + admin auth guard
│   ├── search.py           # POST /v1/search/image · /v1/search/text
│   ├── destinations.py     # GET (public) · POST (admin auto-embed + upsert)
│   └── health.py           # GET /v1/health
├── core/
│   ├── config.py           # env settings + mock-mode detection
│   ├── clip_encoder.py     # CLIP ViT-B/32 wrapper (+ deterministic mock)
│   ├── vector_store.py     # Pinecone wrapper (+ in-memory brute force)
│   └── metadata_store.py   # Supabase wrapper (+ in-memory seed)
├── models/destination.py   # Pydantic v2 contracts
├── scripts/
│   ├── destinations_data.py    # sample catalog / your real data
│   └── index_destinations.py   # offline embedding pipeline
├── db/schema.sql           # Supabase tables + analytics views + RLS
├── Dockerfile              # HF Spaces / Railway
├── requirements.txt        # full (torch + CLIP)
└── requirements-dev.txt    # mock mode (no torch)
```

## Mock mode

The backend auto-detects missing credentials and degrades gracefully:

| Missing | Fallback |
|---------|----------|
| `torch` / CLIP not installed | Deterministic hash pseudo-embeddings (`clip_encoder.py`) |
| `PINECONE_API_KEY` | In-memory brute-force cosine search (`vector_store.py`) |
| `SUPABASE_URL`/`KEY` | In-memory catalog seeded from `destinations_data.py` |

This means you can run the **entire stack locally with zero accounts**:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt      # lightweight, no torch
uvicorn main:app --reload
open http://localhost:8000/docs
```

`GET /v1/health` tells you exactly what is live vs mocked.

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/v1/health` | — | Readiness + which services are live |
| `POST` | `/v1/search/image` | — | Multipart image + filters → ranked cards |
| `POST` | `/v1/search/text` | — | JSON query + filters → ranked cards |
| `GET` | `/v1/destinations/` | — | List active destinations |
| `POST` | `/v1/destinations/` | `x-api-key` admin | Create/update + auto-embed |

### Example — text search

```bash
curl -X POST http://localhost:8000/v1/search/text \
  -H 'Content-Type: application/json' \
  -d '{"query":"snowy mountain honeymoon","budget_max":900000}'
```

### Example — image search

```bash
curl -X POST http://localhost:8000/v1/search/image \
  -F 'file=@beach.jpg' -F 'style=beach' -F 'month=december'
```

## Indexing real data

1. Apply `db/schema.sql` to your Supabase project.
2. Edit `scripts/destinations_data.py` with your catalog (Cloudinary image URLs).
3. Fill `.env` with Pinecone + Supabase keys.
4. `python -m scripts.index_destinations`

## Deploy

**HuggingFace Spaces (free):** create a Docker Space, push this folder, set
`PINECONE_API_KEY` / `SUPABASE_URL` / `SUPABASE_KEY` as Space secrets. The Dockerfile
listens on `7860`.

**Railway ($5/mo, no cold start):** new project from repo, root = `backend/`, it
auto-detects the Dockerfile and injects `$PORT`.

## Performance

CLIP ViT-B/32 inference ≈ 50ms CPU · Pinecone query ≈ 20ms · total backend ≈ 100ms.
Well within the 2-second end-to-end target. For more speed: ViT-B/16 on GPU, or an ONNX
quantized model (~40ms CPU).
