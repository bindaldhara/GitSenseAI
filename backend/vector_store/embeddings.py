"""Sentence Transformers embedding wrapper.

Uses `all-MiniLM-L6-v2` (384-dim) by default — runs locally with no API key
and no usage limits. The model is lazy-loaded on first call.

Why this file exists
--------------------
Isolating the model behind a thin wrapper lets us swap providers later
(e.g. OpenAI, Cohere) without touching chunking or Qdrant code.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Lazy-load the Sentence Transformers model once and cache it."""
    logger.info("Loading embedding model '%s' …", MODEL_NAME)
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Embedding model loaded (dim=%s).", EMBEDDING_DIMENSION)
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return L2-normalized embeddings for a batch of texts.

    Parameters
    ----------
    texts:
        Plain-text strings to embed. Empty list → empty list.

    Returns
    -------
    A list of float vectors, one per input text, each of length
    ``EMBEDDING_DIMENSION`` (384).
    """
    if not texts:
        return []

    model = _get_model()
    # normalize_embeddings=True ensures cosine-distance in Qdrant works with Dot product too.
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings.tolist()
