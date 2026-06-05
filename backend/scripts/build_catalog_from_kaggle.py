"""Build a real Traviante destination catalog from the Kaggle traveler-trip data.

The Kaggle dataset ``rkiattisak/traveler-trip-data`` is **trip-log data** (one row per
traveller trip), not a destination catalog. This script turns it into one by:

  1. Grouping trips by destination → unique ``name`` / ``country``.
  2. Aggregating per-trip ``Accommodation cost + Transportation cost`` into an honest
     INR price band (USD→INR), taking robust low/high percentiles across trips.
  3. Deriving ``best_months`` from the months travellers actually started those trips.
  4. Enriching each destination with a **real Wikipedia summary + lead photo** — this
     fills ``tagline`` (Wikipedia short description), ``description`` (extract) and
     ``images`` with sourced, non-fabricated content.
  5. Inferring ``travel_styles`` from the Wikipedia text via keyword rules so the
     category filters work. ``highlights`` stay empty (no reliable signal).

Output: ``scripts/catalog.json``. ``scripts/destinations_data.py`` loads it when present,
so the running app (and the indexing pipeline) pick up the real catalog automatically.

Usage:
    # Real download (needs ~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY):
    python -m scripts.build_catalog_from_kaggle

    # Offline, against a CSV you already downloaded:
    python -m scripts.build_catalog_from_kaggle --csv /path/to/trips.csv

    # Skip the Wikipedia enrichment (faster; no images/taglines):
    python -m scripts.build_catalog_from_kaggle --no-enrich --limit 10
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests

from models.destination import Destination, TravelStyle

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
logger = logging.getLogger("catalog")

DATASET = "rkiattisak/traveler-trip-data"
CATALOG_PATH = Path(__file__).resolve().parent / "catalog.json"

# Costs in the dataset are in USD; convert to INR for the price band shown on cards.
USD_TO_INR = 86.0
WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKI_ACTION_API = "https://en.wikipedia.org/w/api.php"
WIKI_HEADERS = {"User-Agent": "TravianteCatalogBuilder/1.0 (destination search demo)"}

_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Keyword cues for inferring travel styles from a destination's Wikipedia text.
# Rule-based and transparent — no LLM. A destination can match several styles.
_STYLE_KEYWORDS: dict[TravelStyle, tuple[str, ...]] = {
    TravelStyle.beach: (
        "beach", "island", "coast", "coastal", "lagoon", "reef", "bay", "tropical",
        "atoll", "shore", "seaside", "snorkel", "diving", "surf", "sandy",
    ),
    TravelStyle.adventure: (
        "mountain", "peak", "alps", "alpine", "ski", "skiing", "hike", "hiking",
        "trek", "volcano", "volcanic", "glacier", "rafting", "climbing", "canyon",
        "national park", "trail", "safari", "wilderness", "rainforest",
    ),
    TravelStyle.cultural: (
        "temple", "shrine", "old town", "historic", "ancient", "museum", "heritage",
        "palace", "cathedral", "mosque", "ruins", "medieval", "monument", "unesco",
        "market", "souk", "castle", "fort", "archaeolog",
    ),
    TravelStyle.luxury: (
        "resort", "spa", "luxury", "five-star", "5-star", "villa", "yacht",
        "boutique", "upscale",
    ),
    TravelStyle.honeymoon: (
        "romantic", "honeymoon", "sunset", "couples", "intimate", "picturesque",
    ),
    TravelStyle.family: (
        "theme park", "amusement", "zoo", "aquarium", "family-friendly",
        "playground", "kid",
    ),
}


# ── parsing helpers ─────────────────────────────────────────────────────────
def _clean_name_country(raw: str) -> tuple[str, str] | None:
    """'Phuket, Thailand' -> ('Phuket', 'Thailand'); 'Paris' -> ('Paris', '')."""
    if not raw or not str(raw).strip() or str(raw).strip().lower() == "nan":
        return None
    parts = [p.strip() for p in str(raw).split(",") if p.strip()]
    if not parts:
        return None
    name = parts[0]
    country = parts[-1] if len(parts) > 1 else ""
    return name, country


def _parse_cost(value) -> float | None:
    """Pull a number out of messy cost cells like '$1,200', 'USD 800', '1500'."""
    if value is None:
        return None
    digits = re.sub(r"[^0-9.]", "", str(value))
    if not digits or digits == ".":
        return None
    try:
        cost = float(digits)
    except ValueError:
        return None
    return cost if cost > 0 else None


def _parse_month(value) -> str | None:
    """Extract a lowercase month name from varied date strings."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text or text == "nan":
        return None
    for m in _MONTHS:
        if m in text or m[:3] in text.split():
            return m
    # numeric date: try to read the month component (m/d/Y or Y-m-d)
    nums = re.findall(r"\d+", text)
    for token in nums:
        n = int(token)
        if 1 <= n <= 12 and len(token) <= 2:
            return _MONTHS[n - 1]
    return None


def _slugify(name: str, country: str) -> str:
    base = f"{name}-{country}".lower() if country else name.lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def _classify_styles(text: str) -> list[TravelStyle]:
    """Infer up to 3 travel styles from a destination's text via keyword cues.

    Scores each style by how many of its keywords appear, keeps those with at
    least one hit (highest first). Falls back to 'cultural' — a safe default for a
    real-world place — so every destination matches at least one filter.
    """
    text = text.lower()
    scores: list[tuple[int, TravelStyle]] = []
    for style, keywords in _STYLE_KEYWORDS.items():
        hits = sum(text.count(kw) for kw in keywords)
        if hits:
            scores.append((hits, style))
    scores.sort(key=lambda pair: pair[0], reverse=True)
    styles = [style for _, style in scores[:3]]
    return styles or [TravelStyle.cultural]


def _price_band(costs: list[float]) -> tuple[int, int]:
    """Robust INR low/high from per-trip USD totals, rounded to the nearest 1000."""
    inr = sorted(c * USD_TO_INR for c in costs)
    lo = inr[len(inr) // 10]            # ~10th percentile
    hi = inr[min(len(inr) - 1, (len(inr) * 9) // 10)]  # ~90th percentile
    round_k = lambda x: max(0, int(round(x / 1000.0)) * 1000)
    lo, hi = round_k(lo), round_k(hi)
    return (lo, max(hi, lo))


# ── Wikipedia enrichment ────────────────────────────────────────────────────
def _best_image(data: dict) -> str | None:
    """Pick a lightweight, reliably-served image URL from the summary payload.

    Use the API's ``thumbnail.source`` verbatim — it points at a pre-rendered size
    Wikimedia guarantees exists. (Rewriting the embedded width to an arbitrary value
    often 400s, since only certain widths are pre-generated.) The full-res original
    is the fallback only; it's multi-MB and more prone to rate-limiting.
    """
    return (data.get("thumbnail") or {}).get("source") or (
        data.get("originalimage") or {}
    ).get("source")


def _wiki_summary(query: str, session: requests.Session) -> dict:
    """Return {tagline, description, image} from Wikipedia, or {} on any failure."""
    title = requests.utils.quote(query.replace(" ", "_"))
    try:
        resp = session.get(WIKI_API.format(title=title), timeout=15)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("type") == "disambiguation":
            return {}
        image = _best_image(data)
        return {
            "tagline": (data.get("description") or "").strip(),
            "description": (data.get("extract") or "").strip(),
            "image": image,
        }
    except Exception as exc:  # network / JSON errors are non-fatal
        logger.debug("Wikipedia lookup failed for %r: %s", query, exc)
        return {}


def _wiki_intro(query: str, session: requests.Session) -> str:
    """Full intro paragraph(s) — richer than the summary lede, for style classification.

    The REST summary's ``extract`` is often just the administrative first sentence,
    which lacks touristic cues (e.g. Kyoto reads as "capital city of … Prefecture").
    The action API's ``exintro`` returns the whole intro, where temples/beaches/peaks
    actually appear. Returns "" on any failure.
    """
    try:
        resp = session.get(
            WIKI_ACTION_API,
            params={
                "action": "query", "prop": "extracts", "exintro": 1,
                "explaintext": 1, "redirects": 1, "format": "json", "titles": query,
            },
            timeout=15,
        )
        pages = resp.json().get("query", {}).get("pages", {})
        return next(iter(pages.values()), {}).get("extract", "") if pages else ""
    except Exception as exc:
        logger.debug("Wikipedia intro lookup failed for %r: %s", query, exc)
        return ""


# ── core transform ──────────────────────────────────────────────────────────
def build_catalog(rows: list[dict], enrich: bool, limit: int | None) -> list[Destination]:
    """Group trip rows into Destination records."""
    grouped: dict[str, dict] = {}
    for row in rows:
        nc = _clean_name_country(row.get("Destination"))
        if not nc:
            continue
        name, country = nc
        key = name.lower()
        bucket = grouped.setdefault(
            key, {"name": name, "country": country, "costs": [], "months": []}
        )
        if not bucket["country"] and country:
            bucket["country"] = country
        acc = _parse_cost(row.get("Accommodation cost"))
        trans = _parse_cost(row.get("Transportation cost"))
        total = (acc or 0) + (trans or 0)
        if total > 0:
            bucket["costs"].append(total)
        month = _parse_month(row.get("Start date"))
        if month:
            bucket["months"].append(month)

    # Most-travelled destinations first; cap if a limit was requested.
    ordered = sorted(grouped.values(), key=lambda b: len(b["costs"]), reverse=True)
    if limit:
        ordered = ordered[:limit]

    session = requests.Session()
    session.headers.update(WIKI_HEADERS)

    catalog: list[Destination] = []
    for bucket in ordered:
        name, country = bucket["name"], bucket["country"]
        costs = bucket["costs"] or [50000 / USD_TO_INR]  # fallback if all costs missing
        lo, hi = _price_band(costs)
        months = [m for m, _ in Counter(bucket["months"]).most_common(5)]

        tagline = description = ""
        images: list[str] = []
        intro = ""
        if enrich:
            query = f"{name}, {country}" if country else name
            wiki = _wiki_summary(query, session)
            if not wiki.get("image") and country:
                wiki = {**_wiki_summary(name, session), **{k: v for k, v in wiki.items() if v}}
            tagline = wiki.get("tagline", "")
            description = wiki.get("description", "")[:600]
            if wiki.get("image"):
                images = [wiki["image"]]
            intro = _wiki_intro(query, session) or _wiki_intro(name, session)
            time.sleep(0.2)  # be polite to the Wikipedia API

        # Classify on the richer intro text when available; fall back to the summary.
        styles = _classify_styles(f"{name} {country} {intro or description}")

        try:
            catalog.append(
                Destination(
                    id=_slugify(name, country),
                    name=name,
                    country=country,
                    tagline=tagline,
                    description=description,
                    images=images,
                    price_min_inr=lo,
                    price_max_inr=hi,
                    best_months=months,
                    travel_styles=styles,
                    highlights=[],      # not derivable from trip logs
                )
            )
            logger.info(
                "  %-22s %-16s ₹%d–₹%d  %s  [%s]  img=%s",
                name, country or "—", lo, hi,
                ",".join(months) or "—",
                ",".join(s.value for s in styles),
                "yes" if images else "no",
            )
        except Exception as exc:
            logger.warning("  ✗ skipped %s: %s", name, exc)
    return catalog


# ── data loading ────────────────────────────────────────────────────────────
def _load_rows(csv_path: str | None) -> list[dict]:
    import pandas as pd

    if csv_path:
        df = pd.read_csv(csv_path)
    else:
        import kagglehub

        path = kagglehub.dataset_download(DATASET)
        csvs = list(Path(path).glob("**/*.csv"))
        if not csvs:
            raise SystemExit(f"No CSV found in downloaded dataset at {path}")
        logger.info("Loaded dataset file: %s", csvs[0].name)
        df = pd.read_csv(csvs[0])

    df.columns = [c.strip() for c in df.columns]
    return df.to_dict(orient="records")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="Path to a local trips CSV (skips kagglehub)")
    parser.add_argument("--limit", type=int, default=None, help="Max destinations")
    parser.add_argument("--no-enrich", action="store_true", help="Skip Wikipedia lookup")
    args = parser.parse_args()

    rows = _load_rows(args.csv)
    logger.info("Read %d trip rows. Building catalog…", len(rows))
    catalog = build_catalog(rows, enrich=not args.no_enrich, limit=args.limit)

    if not catalog:
        logger.error("No destinations produced — check the dataset columns.")
        return 1

    payload = [d.model_dump(mode="json") for d in catalog]
    CATALOG_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    logger.info("Wrote %d destinations → %s", len(catalog), CATALOG_PATH)
    logger.info("Restart the API (or run scripts.index_destinations) to use it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
