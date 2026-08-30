"""Qdrant collection management, upsert, and deletion.

Collection layout
-----------------
One collection named ``gitsense`` stores all repository vectors.
Each point carries a ``repository_id`` payload so we can filter or delete
per-repository without touching other repos' data.

Why this file exists
--------------------
Encapsulates all Qdrant HTTP calls behind plain functions so the rest
of the codebase never imports ``qdrant_client`` directly.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from config import settings
from vector_store.embeddings import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

COLLECTION_NAME = "gitsense"
UPSERT_BATCH_SIZE = 64
DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class RetrievedChunk:
    """A code chunk returned by vector similarity search."""

    file_path: str
    language: str
    chunk_kind: str
    symbol_name: str | None
    start_line: int
    end_line: int
    text: str
    score: float


def get_qdrant_client() -> QdrantClient:
    """Create a short-lived Qdrant client (HTTP, no persistent connection pool)."""
    if settings.qdrant_api_key:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(url=settings.qdrant_url)


def _client() -> QdrantClient:
    return get_qdrant_client()


def _ensure_payload_indexes(client: QdrantClient) -> None:
    """Index fields we filter on (required for reliable count/search on Qdrant Cloud)."""
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="repository_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
        logger.info("Ensured Qdrant payload index on repository_id.")
    except UnexpectedResponse as exc:
        logger.debug("repository_id payload index already exists or not needed: %s", exc)
    except Exception:
        logger.warning("Could not create repository_id payload index.", exc_info=True)


def ensure_collection() -> None:
    """Create the code collection if it does not already exist.

    Called once during app startup and before the first upsert.  Uses
    **Cosine** distance which pairs well with L2-normalized embeddings
    produced by FastEmbed (ONNX MiniLM).
    """
    client = _client()
    created = False
    try:
        client.get_collection(COLLECTION_NAME)
        logger.debug("Qdrant collection '%s' already exists.", COLLECTION_NAME)
    except UnexpectedResponse:
        logger.info(
            "Creating Qdrant collection '%s' (dim=%s, cosine).",
            COLLECTION_NAME,
            EMBEDDING_DIMENSION,
        )
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        created = True
    _ensure_payload_indexes(client)
    if created:
        logger.info("Qdrant collection '%s' ready.", COLLECTION_NAME)


def upsert_chunks(
    chunks_with_vectors: list[tuple[dict, list[float]]],
) -> int:
    """Upsert (chunk_payload, vector) pairs into Qdrant.

    Parameters
    ----------
    chunks_with_vectors:
        Each element is ``(payload_dict, embedding_vector)``.

    Returns
    -------
    The total number of points upserted.
    """
    client = _client()
    total = 0

    for batch_start in range(0, len(chunks_with_vectors), UPSERT_BATCH_SIZE):
        batch = chunks_with_vectors[batch_start : batch_start + UPSERT_BATCH_SIZE]
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
            for payload, vector in batch
        ]
        client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
        total += len(points)

    logger.info("Upserted %s points into Qdrant collection '%s'.", total, COLLECTION_NAME)
    return total


def delete_repository_points(repository_id: int) -> int:
    """Delete all Qdrant points belonging to a repository.

    Uses a filter on the ``repository_id`` payload field.

    Returns
    -------
    Approximate count of deleted points (Qdrant does not return exact
    counts for filtered deletes, so we count beforehand).
    """
    client = _client()
    repo_filter = Filter(
        must=[FieldCondition(key="repository_id", match=MatchValue(value=repository_id))]
    )

    # Count first for logging / summary.
    try:
        count_result = client.count(
            collection_name=COLLECTION_NAME,
            count_filter=repo_filter,
            exact=True,
        )
        existing_count = count_result.count
    except Exception:
        existing_count = 0

    if existing_count == 0:
        logger.info("No Qdrant points to delete for repository_id=%s.", repository_id)
        return 0

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=repo_filter,
        wait=True,
    )
    logger.info(
        "Deleted ~%s Qdrant points for repository_id=%s.",
        existing_count,
        repository_id,
    )
    return existing_count


def count_repository_points(repository_id: int) -> int:
    """Return the exact number of points stored for a repository."""
    client = _client()
    repo_filter = Filter(
        must=[FieldCondition(key="repository_id", match=MatchValue(value=int(repository_id)))]
    )
    try:
        result = client.count(
            collection_name=COLLECTION_NAME,
            count_filter=repo_filter,
            exact=True,
        )
        return result.count
    except Exception:
        logger.error(
            "Qdrant count failed for repository_id=%s — check QDRANT_URL/API key and payload index.",
            repository_id,
            exc_info=True,
        )
        try:
            total = client.count(collection_name=COLLECTION_NAME, exact=True).count
            logger.error(
                "Collection '%s' has %s total points (unfiltered).",
                COLLECTION_NAME,
                total,
            )
        except Exception:
            logger.error("Could not read total Qdrant collection count.", exc_info=True)
        return 0


def search_repository_chunks(
    repository_id: int,
    query_vector: list[float],
    *,
    top_k: int = DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    """Return the top-k most similar chunks for a repository.

    Filters strictly on ``repository_id`` so cross-repo leakage cannot occur.
    """
    client = _client()
    repo_filter = Filter(
        must=[FieldCondition(key="repository_id", match=MatchValue(value=repository_id))]
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=repo_filter,
        limit=top_k,
        with_payload=True,
    )

    chunks: list[RetrievedChunk] = []
    for point in results.points:
        payload = point.payload or {}
        chunks.append(
            RetrievedChunk(
                file_path=str(payload.get("file_path", "")),
                language=str(payload.get("language", "")),
                chunk_kind=str(payload.get("chunk_kind", "")),
                symbol_name=payload.get("symbol_name"),
                start_line=int(payload.get("start_line", 0)),
                end_line=int(payload.get("end_line", 0)),
                text=str(payload.get("text", "")),
                score=float(point.score or 0.0),
            )
        )

    logger.info(
        "Retrieved %s chunks for repository_id=%s (top_k=%s).",
        len(chunks),
        repository_id,
        top_k,
    )
    return chunks
