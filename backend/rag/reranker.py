"""Cross-encoder reranking for retrieved code chunks.

Bi-encoder retrieval (vectors + BM25) is fast but approximate. A cross-encoder
scores each (query, chunk) pair jointly and produces a more accurate ranking
before chunks are sent to the LLM.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from functools import lru_cache

from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from config import settings
from vector_store.qdrant_store import RetrievedChunk

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_cross_encoder() -> HuggingFaceCrossEncoder:
    logger.info("Loading cross-encoder reranker model '%s' …", settings.rerank_model)
    return HuggingFaceCrossEncoder(model_name=settings.rerank_model)


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
    pairs = [(question, chunk.text) for chunk in chunks]
    scores = encoder.score(pairs)

    ranked = sorted(zip(chunks, scores), key=lambda item: item[1], reverse=True)[:top_k]
    reranked = [replace(chunk, score=float(score)) for chunk, score in ranked]

    logger.info(
        "Cross-encoder reranked %s chunks down to %s for query preview=%r.",
        len(chunks),
        len(reranked),
        question[:80],
    )
    return reranked
