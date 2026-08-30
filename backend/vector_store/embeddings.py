"""ONNX embedding wrapper via FastEmbed.

Uses ``sentence-transformers/all-MiniLM-L6-v2`` (384-dim) through ONNX Runtime
instead of PyTorch. Vectors stay compatible with the existing Qdrant collection.
No API key, unlimited local usage.

Why this file exists
--------------------
Isolating the model behind a thin wrapper lets us swap providers later
without touching chunking or Qdrant code.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


def _cache_dir() -> str | None:
    return os.environ.get("FASTEMBED_CACHE_PATH")


@lru_cache(maxsize=1)
def _get_model() -> TextEmbedding:
    """Lazy-load the ONNX embedding model once and cache it."""
    logger.info("Loading FastEmbed ONNX model '%s' …", MODEL_NAME)
    kwargs: dict = {"model_name": MODEL_NAME, "threads": 1}
    cache_dir = _cache_dir()
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    model = TextEmbedding(**kwargs)
    logger.info("Embedding model loaded (dim=%s, engine=onnx).", EMBEDDING_DIMENSION)
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

    embeddings = [_vector_to_list(vector) for vector in _get_model().embed(texts)]
    return embeddings


def _vector_to_list(vector) -> list[float]:
    if hasattr(vector, "tolist"):
        return vector.tolist()
    return [float(value) for value in vector]
