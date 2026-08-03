"""Redis-backed semantic cache for repository chat responses.

Unlike exact-match caches, semantic caching embeds the user question and
returns a prior answer when a previously cached question is *similar enough*
(cosine similarity on Sentence Transformer embeddings).
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cache.analytics import adjust_entry_count, record_cache_hit, record_cache_miss, record_cache_store
from cache.redis_client import get_redis_client
from config import settings
from vector_store.embeddings import embed_texts

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CachedChatResponse:
    answer: str
    sources: list[dict[str, Any]]
    model: str
    retrieval_mode: str
    similarity: float
    cached_question: str


def _repo_index_key(repository_id: int) -> str:
    return f"gitsense:semantic_cache:repo:{repository_id}:index"


def _entry_key(entry_id: str) -> str:
    return f"gitsense:semantic_cache:entry:{entry_id}"


def _normalize_question(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    return float(sum(a * b for a, b in zip(left, right, strict=True)))


def lookup_cached_chat(
    repository_id: int,
    question: str,
    question_embedding: list[float] | None = None,
) -> CachedChatResponse | None:
    """Return a cached chat response when a similar question exists."""
    if not settings.semantic_cache_enabled:
        return None

    try:
        client = get_redis_client()
        entry_ids = client.lrange(_repo_index_key(repository_id), 0, -1)
        if not entry_ids:
            record_cache_miss(repository_id=repository_id, question=question, similarity=None)
            return None

        query_embedding = question_embedding or embed_texts([question])[0]
        normalized_question = _normalize_question(question)
        best_similarity = -1.0
        best_payload: dict[str, Any] | None = None

        for entry_id in entry_ids:
            raw = client.get(_entry_key(entry_id))
            if not raw:
                continue
            payload = json.loads(raw)
            cached_question = str(payload.get("question", ""))
            if _normalize_question(cached_question) == normalized_question:
                best_similarity = 1.0
                best_payload = payload
                break

            cached_embedding = payload.get("embedding") or []
            if not cached_embedding:
                continue
            similarity = _cosine_similarity(query_embedding, cached_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_payload = payload

        threshold = settings.semantic_cache_similarity_threshold
        if best_payload is None or best_similarity < threshold:
            record_cache_miss(
                repository_id=repository_id,
                question=question,
                similarity=best_similarity if best_similarity >= 0 else None,
            )
            logger.info(
                "Semantic cache miss for repository_id=%s (best_similarity=%.3f, threshold=%.3f).",
                repository_id,
                max(best_similarity, 0.0),
                threshold,
            )
            return None

        record_cache_hit(repository_id=repository_id, question=question, similarity=best_similarity)
        logger.info(
            "Semantic cache hit for repository_id=%s (similarity=%.3f).",
            repository_id,
            best_similarity,
        )
        return CachedChatResponse(
            answer=str(best_payload["answer"]),
            sources=list(best_payload.get("sources") or []),
            model=str(best_payload.get("model", "")),
            retrieval_mode=str(best_payload.get("retrieval_mode", "vector")),
            similarity=best_similarity,
            cached_question=str(best_payload.get("question", "")),
        )
    except Exception:
        logger.warning("Semantic cache lookup failed; continuing without cache.", exc_info=True)
        return None


def store_cached_chat(
    repository_id: int,
    question: str,
    *,
    question_embedding: list[float] | None,
    answer: str,
    sources: list[dict[str, Any]],
    model: str,
    retrieval_mode: str,
) -> None:
    """Persist a chat response for future semantic lookups."""
    if not settings.semantic_cache_enabled:
        return

    try:
        client = get_redis_client()
        entry_id = uuid.uuid4().hex
        embedding = question_embedding or embed_texts([question])[0]
        payload = {
            "repository_id": repository_id,
            "question": question,
            "embedding": embedding,
            "answer": answer,
            "sources": sources,
            "model": model,
            "retrieval_mode": retrieval_mode,
            "created_at": datetime.now(UTC).isoformat(),
        }
        ttl = settings.semantic_cache_ttl_seconds
        client.set(_entry_key(entry_id), json.dumps(payload), ex=ttl)
        index_key = _repo_index_key(repository_id)
        client.lpush(index_key, entry_id)
        client.ltrim(index_key, 0, settings.semantic_cache_max_entries_per_repo - 1)
        client.expire(index_key, ttl)
        adjust_entry_count(1)
        record_cache_store(repository_id=repository_id, question=question)
    except Exception:
        logger.warning("Failed to store semantic cache entry.", exc_info=True)


def invalidate_repository_cache(repository_id: int) -> int:
    """Delete all semantic cache entries for a repository."""
    try:
        client = get_redis_client()
        index_key = _repo_index_key(repository_id)
        entry_ids = client.lrange(index_key, 0, -1)
        if not entry_ids:
            return 0

        keys = [_entry_key(entry_id) for entry_id in entry_ids]
        deleted = client.delete(*keys, index_key)
        removed_entries = len(entry_ids)
        adjust_entry_count(-removed_entries)
        logger.info("Invalidated %s semantic cache entries for repository_id=%s.", removed_entries, repository_id)
        return removed_entries
    except Exception:
        logger.warning("Failed to invalidate semantic cache for repository_id=%s.", repository_id, exc_info=True)
        return 0


def clear_all_semantic_cache() -> int:
    """Delete all semantic cache keys."""
    try:
        client = get_redis_client()
        removed = 0
        for pattern in ("gitsense:semantic_cache:entry:*", "gitsense:semantic_cache:repo:*"):
            for key in client.scan_iter(match=pattern):
                client.delete(key)
                removed += 1
        client.set("gitsense:cache:stats:entries", 0)
        return removed
    except Exception:
        logger.warning("Failed to clear semantic cache.", exc_info=True)
        return 0
