"""CLIP ViT-B/32 wrapper — the heart of the ML system.

Both images *and* text are projected into the **same 512-dimensional space**, so a
beach photo and the text "tropical beach honeymoon" land near each other. That is
CLIP's core innovation — no fine-tuning needed.

If PyTorch / CLIP is not installed (e.g. a lightweight dev machine), the encoder falls
back to a **deterministic hash-based pseudo-embedding** so the rest of the stack — API,
Pinecone wiring, frontend — can be developed and tested end-to-end. The pseudo encoder
is clearly flagged via ``is_mock`` and must never be used in production.
"""
from __future__ import annotations

import hashlib
import io
import logging

import numpy as np

logger = logging.getLogger(__name__)


class ClipEncoder:
    def __init__(self, model_name: str = "ViT-B/32", device: str = "auto") -> None:
        self.model_name = model_name
        self.embedding_dim = 512
        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self.is_mock = False
        self.device = self._resolve_device(device)
        self._load()

    # ── lifecycle ──────────────────────────────────────────────────────────
    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _load(self) -> None:
        """Load real CLIP once; fall back to the mock encoder on any failure."""
        try:
            import clip  # type: ignore
            import torch  # noqa: F401

            logger.info("Loading CLIP %s on %s ...", self.model_name, self.device)
            self._model, self._preprocess = clip.load(self.model_name, device=self.device)
            self._model.eval()
            self._tokenizer = clip.tokenize
            logger.info("CLIP loaded.")
        except Exception as exc:  # pragma: no cover - depends on env
            logger.warning(
                "CLIP unavailable (%s). Falling back to MOCK encoder — "
                "embeddings are deterministic hashes, NOT semantic.",
                exc,
            )
            self.is_mock = True

    # ── encoding ───────────────────────────────────────────────────────────
    def encode_image(self, data: bytes) -> list[float]:
        """Encode raw image bytes into a normalised 512-d vector."""
        if self.is_mock:
            return self._mock_vector(data)

        import torch
        from PIL import Image

        image = Image.open(io.BytesIO(data)).convert("RGB")
        tensor = self._preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feats = self._model.encode_image(tensor).float()
        return self._normalise(feats)

    def encode_text(self, text: str) -> list[float]:
        """Encode a natural-language query into a normalised 512-d vector."""
        if self.is_mock:
            return self._mock_vector(text.encode("utf-8"))

        import torch

        # truncate=True clips text past CLIP's 77-token context instead of raising —
        # catalog descriptions (e.g. Wikipedia extracts) routinely exceed it.
        tokens = self._tokenizer([text], truncate=True).to(self.device)
        with torch.no_grad():
            feats = self._model.encode_text(tokens).float()
        return self._normalise(feats)

    def encode_image_url(self, url: str) -> list[float]:
        """Download an image URL and encode it (used by the indexing pipeline)."""
        if self.is_mock:
            return self._mock_vector(url.encode("utf-8"))

        import requests

        # A descriptive User-Agent is required by some hosts (e.g. Wikimedia
        # returns 403 for the default urllib/requests agent).
        headers = {"User-Agent": "Traviante/1.0 (destination visual search)"}
        resp = requests.get(url, timeout=30, headers=headers)
        resp.raise_for_status()
        return self.encode_image(resp.content)

    def encode_images_averaged(self, urls: list[str]) -> list[float]:
        """Average the embeddings of several images into one destination vector."""
        if not urls:
            raise ValueError("At least one image URL is required.")
        vectors = np.array([self.encode_image_url(u) for u in urls], dtype=np.float32)
        avg = vectors.mean(axis=0)
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm
        return avg.tolist()

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _normalise(feats) -> list[float]:
        feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.cpu().numpy().astype("float32")[0].tolist()

    def _mock_vector(self, seed: bytes) -> list[float]:
        """Deterministic unit vector derived from a hash of the input.

        Same input → same vector, so similarity search stays internally
        consistent (a query re-encodes to the same point as when indexed).
        """
        digest = hashlib.sha256(seed).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
        vec = rng.standard_normal(self.embedding_dim).astype("float32")
        vec /= np.linalg.norm(vec)
        return vec.tolist()
