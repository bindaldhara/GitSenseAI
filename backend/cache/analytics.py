"""Semantic cache analytics stored in Redis."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from cache.redis_client import get_redis_client
from config import settings

logger = logging.getLogger(__name__)

STATS_HITS_KEY = "gitsense:cache:stats:hits"
STATS_MISSES_KEY = "gitsense:cache:stats:misses"
STATS_STORES_KEY = "gitsense:cache:stats:stores"
STATS_ENTRIES_KEY = "gitsense:cache:stats:entries"
EVENTS_KEY = "gitsense:cache:events"
MAX_EVENTS = 50


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _append_event(event_type: str, *, repository_id: int, question: str, similarity: float | None = None) -> None:
    if not settings.semantic_cache_enabled:
        return

    try:
        client = get_redis_client()
        payload = {
            "type": event_type,
            "repository_id": repository_id,
            "question": question[:200],
            "similarity": similarity,
            "timestamp": _now_iso(),
        }
        client.lpush(EVENTS_KEY, json.dumps(payload))
        client.ltrim(EVENTS_KEY, 0, MAX_EVENTS - 1)
    except Exception:
        logger.warning("Failed to record cache analytics event.", exc_info=True)


def record_cache_hit(*, repository_id: int, question: str, similarity: float) -> None:
    try:
        client = get_redis_client()
        client.incr(STATS_HITS_KEY)
        _append_event("hit", repository_id=repository_id, question=question, similarity=similarity)
    except Exception:
        logger.warning("Failed to record cache hit.", exc_info=True)


def record_cache_miss(*, repository_id: int, question: str, similarity: float | None = None) -> None:
    try:
        client = get_redis_client()
        client.incr(STATS_MISSES_KEY)
        _append_event("miss", repository_id=repository_id, question=question, similarity=similarity)
    except Exception:
        logger.warning("Failed to record cache miss.", exc_info=True)


def record_cache_store(*, repository_id: int, question: str) -> None:
    try:
        client = get_redis_client()
        client.incr(STATS_STORES_KEY)
        _append_event("store", repository_id=repository_id, question=question)
    except Exception:
        logger.warning("Failed to record cache store.", exc_info=True)


def adjust_entry_count(delta: int) -> None:
    if delta == 0:
        return
    try:
        client = get_redis_client()
        if delta > 0:
            client.incrby(STATS_ENTRIES_KEY, delta)
        else:
            client.decrby(STATS_ENTRIES_KEY, abs(delta))
    except Exception:
        logger.warning("Failed to adjust cache entry count.", exc_info=True)


def get_cache_analytics() -> dict:
    try:
        client = get_redis_client()
        hits = int(client.get(STATS_HITS_KEY) or 0)
        misses = int(client.get(STATS_MISSES_KEY) or 0)
        stores = int(client.get(STATS_STORES_KEY) or 0)
        entries = max(int(client.get(STATS_ENTRIES_KEY) or 0), 0)
        lookups = hits + misses
        hit_rate = round((hits / lookups) * 100, 1) if lookups else 0.0

        raw_events = client.lrange(EVENTS_KEY, 0, MAX_EVENTS - 1)
        events = []
        for item in raw_events:
            try:
                events.append(json.loads(item))
            except json.JSONDecodeError:
                continue

        return {
            "enabled": settings.semantic_cache_enabled,
            "similarity_threshold": settings.semantic_cache_similarity_threshold,
            "ttl_seconds": settings.semantic_cache_ttl_seconds,
            "max_entries_per_repo": settings.semantic_cache_max_entries_per_repo,
            "hits": hits,
            "misses": misses,
            "stores": stores,
            "entries": entries,
            "lookups": lookups,
            "hit_rate_percent": hit_rate,
            "recent_events": events,
        }
    except Exception as exc:
        logger.warning("Failed to load cache analytics.", exc_info=True)
        return {
            "enabled": settings.semantic_cache_enabled,
            "similarity_threshold": settings.semantic_cache_similarity_threshold,
            "ttl_seconds": settings.semantic_cache_ttl_seconds,
            "max_entries_per_repo": settings.semantic_cache_max_entries_per_repo,
            "hits": 0,
            "misses": 0,
            "stores": 0,
            "entries": 0,
            "lookups": 0,
            "hit_rate_percent": 0.0,
            "recent_events": [],
            "error": str(exc),
        }


def reset_cache_analytics() -> None:
    client = get_redis_client()
    client.delete(STATS_HITS_KEY, STATS_MISSES_KEY, STATS_STORES_KEY, STATS_ENTRIES_KEY, EVENTS_KEY)
