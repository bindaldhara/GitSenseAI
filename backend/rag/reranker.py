"""Cross-encoder reranking for retrieved code chunks.

Bi-encoder retrieval (vectors + BM25) is fast but approximate. A cross-encoder
scores each (query, chunk) pair jointly and produces a more accurate ranking
before chunks are sent to the LLM.

Uses FastEmbed ONNX (``Xenova/ms-marco-MiniLM-L-6-v2``) so rerank does not
load PyTorch.
"""

from __future__ import annotations

import logging
import os
from dataclasses import replace
from functools import lru_cache

from fastembed.rerank.cross_encoder import TextCrossEncoder

from config import settings
from vector_store.qdrant_store import RetrievedChunk

logger = logging.getLogger(__name__)

# Hugging Face PyTorch id → FastEmbed ONNX id (same MiniLM-L6 reranker).
_RERANK_MODEL_ALIASES = {
    "cross-encoder/ms-marco-MiniLM-L-6-v2": "Xenova/ms-marco-MiniLM-L-6-v2",
}


def _rerank_model_name() -> str:
    return _RERANK_MODEL_ALIASES.get(settings.rerank_model, settings.rerank_model)


@lru_cache(maxsize=1)
def _get_cross_encoder() -> TextCrossEncoder:
    model_name = _rerank_model_name()
    logger.info("Loading FastEmbed ONNX reranker '%s' …", model_name)
    kwargs: dict = {"model_name": model_name, "threads": 1}
    cache_dir = os.environ.get("FASTEMBED_CACHE_PATH")
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    return TextCrossEncoder(**kwargs)


def rerank_retrieved_chunks(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    top_k: int,
) -> list[RetrievedChunk]:
    """Rerank retrieved chunks with a cross-encoder and return the top-k."""
    if not chunks:
        return []

    if len(chunks) == 1:
        return chunks[:top_k]

    encoder = _get_cross_encoder()
    documents = [chunk.text for chunk in chunks]
    scores = list(encoder.rerank(question, documents))

    ranked = sorted(zip(chunks, scores), key=lambda item: item[1], reverse=True)[:top_k]
    reranked = [replace(chunk, score=float(score)) for chunk, score in ranked]

    logger.info(
        "Cross-encoder reranked %s chunks down to %s for query preview=%r.",
        len(chunks),
        len(reranked),
        question[:80],
    )
    return reranked
