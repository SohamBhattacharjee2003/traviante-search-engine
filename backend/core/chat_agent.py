"""Traviante conversational concierge — the AI/ML interaction layer.

Two intelligence tiers, chosen automatically:

  • **LLM mode** (when ``GROQ_API_KEY`` is set): a Groq-hosted Llama model runs a
    tool-calling loop. It reasons about the traveller's intent, extracts structured
    preferences, and calls the ``search_destinations`` tool — which executes the
    *same* CLIP + lexical ranking pipeline the REST API uses (``core.search_engine``)
    — then narrates the matches conversationally.

  • **Offline NLU mode** (no key): a deterministic heuristic extracts budget / month
    / style from the message, runs the identical search, and returns a templated but
    genuinely helpful reply. This keeps the whole stack runnable with zero credentials.

Either way the response carries the structured ``filters`` the agent inferred and the
``results`` it surfaced, so the frontend can render destination cards inline in chat.
"""
from __future__ import annotations

import json
import logging
import re
import time

import httpx

from core.clip_encoder import ClipEncoder
from core.config import Settings
from core.metadata_store import MetadataStore
from core.search_engine import rank_image, rank_text
from core.vector_store import VectorStore
from models.destination import (
    ChatMessage,
    ChatResponse,
    DestinationResult,
    SearchFilters,
    TravelStyle,
)

logger = logging.getLogger(__name__)

_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Natural-language cues → a canonical travel style. Lets the offline agent map
# "romantic getaway" → honeymoon, "hiking trip" → adventure, etc.
_STYLE_CUES: dict[TravelStyle, tuple[str, ...]] = {
    TravelStyle.honeymoon: ("honeymoon", "romantic", "romance", "couple", "anniversary"),
    TravelStyle.adventure: ("adventure", "hike", "hiking", "trek", "trekking", "ski", "skiing", "surf", "dive", "diving", "rafting"),
    TravelStyle.family: ("family", "kids", "children", "kid-friendly"),
    TravelStyle.cultural: ("cultural", "culture", "history", "historic", "temple", "heritage", "museum"),
    TravelStyle.beach: ("beach", "beaches", "island", "coast", "coastal", "sea", "ocean", "tropical"),
    TravelStyle.luxury: ("luxury", "luxurious", "premium", "five star", "5 star", "lavish", "indulgent"),
}

_SUGGESTION_BANK = [
    "Snowy mountain honeymoon",
    "Tropical beach on a budget",
    "Cultural city break in October",
    "Adventure trip with hiking",
    "Luxury island escape",
]


def _extract_filters_heuristic(text: str, base: SearchFilters) -> SearchFilters:
    """Best-effort structured-preference extraction without an LLM."""
    t = text.lower()
    budget_max = base.budget_max
    month = base.month
    style = base.style

    # Budget: "under 2 lakh", "₹3L", "200000", "150k".
    if budget_max is None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l\b)", t)
        if m:
            budget_max = int(float(m.group(1)) * 100_000)
        elif (m := re.search(r"₹\s*(\d[\d,]*)", t)):
            budget_max = int(m.group(1).replace(",", ""))
        elif (m := re.search(r"\b(\d+)\s*k\b", t)):
            budget_max = int(m.group(1)) * 1_000

    if month is None:
        for mo in _MONTHS:
            if mo in t or mo[:3] in re.findall(r"[a-z]{3,}", t):
                if mo in t:
                    month = mo
                    break

    if style is None:
        for cue_style, cues in _STYLE_CUES.items():
            if any(c in t for c in cues):
                style = cue_style
                break

    return SearchFilters(
        budget_max=budget_max,
        month=month,
        style=style,
        group_size=base.group_size,
    )


def _result_brief(results: list[DestinationResult]) -> list[dict]:
    """Compact JSON view of results — fed to the LLM as the tool's return value."""
    return [
        {
            "name": r.name,
            "country": r.country,
            "tagline": r.tagline,
            "price_inr": [r.price_min_inr, r.price_max_inr],
            "best_months": r.best_months[:4],
            "styles": [s.value for s in r.travel_styles],
            "match_pct": round(r.score * 100),
        }
        for r in results
    ]


class ChatAgent:
    """Stateless per-request concierge. Conversation history is passed in each call."""

    SEARCH_TOOL = {
        "type": "function",
        "function": {
            "name": "search_destinations",
            "description": (
                "Search Traviante's destination catalog by a free-text vibe/description "
                "plus optional structured filters. Call this whenever the traveller asks "
                "for trip ideas or refines their preferences."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A vivid description of the desired trip, e.g. 'snowy alpine honeymoon with cosy chalets'.",
                    },
                    "budget_max": {
                        "type": "integer",
                        "description": "Maximum per-person budget in INR, if the traveller stated one.",
                    },
                    "month": {
                        "type": "string",
                        "enum": _MONTHS,
                        "description": "Preferred travel month, lowercase, if mentioned.",
                    },
                    "style": {
                        "type": "string",
                        "enum": [s.value for s in TravelStyle],
                        "description": "Travel style if clear from the conversation.",
                    },
                },
                "required": ["query"],
            },
        },
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = settings.groq_enabled

    # ── public API ──────────────────────────────────────────────────────────
    async def respond_text(
        self,
        message: str,
        history: list[ChatMessage],
        filters: SearchFilters,
        encoder: ClipEncoder,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
    ) -> ChatResponse:
        started = time.perf_counter()

        def run_search(query: str, f: SearchFilters) -> list[DestinationResult]:
            embedding = None if encoder.is_mock else encoder.encode_text(query or message)
            return rank_text(
                query or message,
                embedding,
                f,
                vector_store,
                metadata_store,
                self.settings.default_top_k,
            )

        if self.enabled:
            try:
                reply, results, out_filters = await self._respond_llm(
                    message, history, filters, run_search, metadata_store
                )
                return self._finish(
                    reply, results, out_filters, used_llm=True, started=started
                )
            except Exception as exc:  # network / key / quota — degrade gracefully
                logger.warning("Groq call failed (%s); using offline NLU.", exc)

        reply, results, out_filters = self._respond_offline(message, filters, run_search)
        return self._finish(reply, results, out_filters, used_llm=False, started=started)

    async def respond_image(
        self,
        results: list[DestinationResult],
        caption: str,
        history: list[ChatMessage],
        filters: SearchFilters,
        started: float,
    ) -> ChatResponse:
        """Narrate the matches for an uploaded photo (search already ran on CLIP)."""
        if self.enabled and results:
            try:
                reply = await self._narrate_image_llm(results, caption, history)
                return self._finish(reply, results, filters, used_llm=True, started=started)
            except Exception as exc:
                logger.warning("Groq narration failed (%s); using template.", exc)

        reply = self._narrate_image_offline(results)
        return self._finish(reply, results, filters, used_llm=False, started=started)

    # ── LLM (Groq) path ─────────────────────────────────────────────────────
    def _system_prompt(self, metadata_store: MetadataStore) -> str:
        try:
            catalog = metadata_store.list_active()
        except Exception:
            catalog = []
        sample = ", ".join(f"{d.name} ({d.country})" for d in catalog[:14])
        return (
            "You are Aria, Traviante's warm, knowledgeable travel concierge for premium "
            "trips (prices are in Indian Rupees, ₹). Help the traveller discover "
            "destinations from Traviante's curated catalog.\n\n"
            "Guidelines:\n"
            "- Be concise, friendly and specific — 2-4 sentences, no purple prose.\n"
            "- When the traveller describes any kind of trip, CALL the search_destinations "
            "tool to find real matches before recommending. Never invent destinations that "
            "aren't returned by the tool.\n"
            "- After the tool returns, reference the matches by name and explain briefly why "
            "they fit. Mention price ranges or best months when useful.\n"
            "- If their request is vague, ask ONE crisp follow-up question to narrow it down.\n"
            f"- A sample of the catalog: {sample or 'various global destinations'}."
        )

    def _history_to_messages(self, history: list[ChatMessage]) -> list[dict]:
        out: list[dict] = []
        for m in history[-12:]:
            content = m.content
            if m.image and m.role.value == "user":
                content = (content + " [shared a photo]").strip()
            if content:
                out.append({"role": m.role.value, "content": content})
        return out

    async def _respond_llm(
        self,
        message: str,
        history: list[ChatMessage],
        filters: SearchFilters,
        run_search,
        metadata_store: MetadataStore,
    ) -> tuple[str, list[DestinationResult], SearchFilters]:
        messages: list[dict] = [{"role": "system", "content": self._system_prompt(metadata_store)}]
        messages += self._history_to_messages(history)
        messages.append({"role": "user", "content": message})

        results: list[DestinationResult] = []
        out_filters = filters

        # Up to two tool rounds, then force a final prose answer.
        for round_idx in range(3):
            force_final = round_idx == 2
            data = await self._groq(
                messages,
                tools=None if force_final else [self.SEARCH_TOOL],
                tool_choice=None if force_final else "auto",
            )
            choice = data["choices"][0]["message"]
            tool_calls = choice.get("tool_calls")

            if tool_calls and not force_final:
                messages.append(choice)  # assistant turn carrying the tool calls
                for tc in tool_calls:
                    try:
                        args = json.loads(tc["function"].get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    out_filters = self._merge_filters(out_filters, args)
                    results = run_search(args.get("query", message), out_filters)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": "search_destinations",
                            "content": json.dumps(
                                {"matches": _result_brief(results)}, ensure_ascii=False
                            ),
                        }
                    )
                continue

            reply = (choice.get("content") or "").strip()
            if not reply:
                reply = self._narrate_image_offline(results) if results else (
                    "I'd love to help plan this — could you tell me a bit more about the vibe you're after?"
                )
            return reply, results, out_filters

        return (
            self._narrate_image_offline(results) if results else
            "Tell me a little more about the kind of trip you're dreaming of?"
        ), results, out_filters

    async def _narrate_image_llm(
        self, results: list[DestinationResult], caption: str, history: list[ChatMessage]
    ) -> str:
        brief = _result_brief(results)
        prompt = (
            "The traveller uploaded a photo of a place they love. Our visual model (CLIP) "
            "matched it to these Traviante destinations (most similar first):\n"
            f"{json.dumps(brief, ensure_ascii=False)}\n\n"
            "In 2-3 warm sentences, tell them what vibe their photo gives off and which of "
            "these destinations capture it. Reference the top matches by name."
        )
        messages = [
            {"role": "system", "content": "You are Aria, Traviante's travel concierge. Prices are in ₹."},
            {"role": "user", "content": prompt},
        ]
        data = await self._groq(messages, tools=None, tool_choice=None)
        return (data["choices"][0]["message"].get("content") or "").strip() or self._narrate_image_offline(results)

    async def _groq(self, messages: list[dict], tools, tool_choice) -> dict:
        payload: dict = {
            "model": self.settings.groq_model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 600,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.settings.groq_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code >= 400:
                # Surface the provider's error body — Groq explains *why* (bad tool
                # args, context length, etc.) so the warning log is actionable.
                raise RuntimeError(f"Groq {resp.status_code}: {resp.text[:500]}")
            return resp.json()

    @staticmethod
    def _merge_filters(base: SearchFilters, args: dict) -> SearchFilters:
        style = base.style
        if args.get("style"):
            try:
                style = TravelStyle(args["style"])
            except ValueError:
                pass
        month = args.get("month") or base.month
        if month:
            month = str(month).lower()
        return SearchFilters(
            budget_max=args.get("budget_max") or base.budget_max,
            month=month if month in _MONTHS else base.month,
            style=style,
            group_size=base.group_size,
        )

    # ── offline NLU path ────────────────────────────────────────────────────
    def _respond_offline(
        self, message: str, filters: SearchFilters, run_search
    ) -> tuple[str, list[DestinationResult], SearchFilters]:
        out_filters = _extract_filters_heuristic(message, filters)
        results = run_search(message, out_filters)
        reply = self._compose_offline_reply(message, out_filters, results)
        return reply, results, out_filters

    @staticmethod
    def _compose_offline_reply(
        message: str, filters: SearchFilters, results: list[DestinationResult]
    ) -> str:
        if not results:
            return (
                "I couldn't find a match for that just yet. Try describing the vibe — "
                "say a beach honeymoon, a snowy adventure, or a cultural city break — "
                "and I'll pull up destinations."
            )
        bits: list[str] = []
        if filters.style:
            bits.append(f"{filters.style.value}")
        if filters.month:
            bits.append(f"around {filters.month.title()}")
        if filters.budget_max:
            bits.append(f"under ₹{filters.budget_max // 100_000}L")
        lead = "Great — based on " + (
            "your " + ", ".join(bits) if bits else "what you described"
        ) + ", here's what I'd recommend:"
        top = results[0]
        why = top.match_reason or f"a standout for {top.country}"
        return (
            f"{lead} **{top.name}** ({top.country}) stands out — {why.lower()}, "
            f"from about ₹{top.price_min_inr // 100_000}L. "
            f"I've pulled {len(results)} matches below — tell me what to adjust."
        )

    @staticmethod
    def _narrate_image_offline(results: list[DestinationResult]) -> str:
        if not results:
            return "I couldn't find a close visual match — want to describe the place instead?"
        names = ", ".join(r.name for r in results[:3])
        top = results[0]
        return (
            f"Your photo's vibe is a strong match for **{top.name}** "
            f"({round(top.score * 100)}% similar). You might also love {names}. "
            "Here are the closest destinations:"
        )

    # ── shared ──────────────────────────────────────────────────────────────
    def _finish(
        self,
        reply: str,
        results: list[DestinationResult],
        filters: SearchFilters,
        used_llm: bool,
        started: float,
    ) -> ChatResponse:
        return ChatResponse(
            reply=reply,
            results=results,
            filters=filters,
            suggestions=[] if results else _SUGGESTION_BANK[:4],
            used_llm=used_llm,
            mock_mode=self.settings.mock_mode,
            query_time_ms=int((time.perf_counter() - started) * 1000),
        )
