"""Embedding ingestion orchestrator — chunk → embed → upsert.

This module is the single entry point that the rest of the codebase calls
when it needs to create or refresh embeddings for a repository.
"""

from __future__ import annotations

import logging
from pathlib import Path

from vector_store.chunker import chunk_repository
from vector_store.embeddings import embed_texts
from vector_store.qdrant_store import (
    count_repository_points,
    delete_repository_points,
    ensure_collection,
    upsert_chunks,
)

logger = logging.getLogger(__name__)

# Batch size for embedding calls (controls peak memory).
EMBED_BATCH_SIZE = 64


def embed_repository(repository_id: int, clone_path: str | Path) -> dict:
    """Full pipeline: chunk the repo, embed every chunk, upsert into Qdrant.

    Any existing points for this repository are deleted first so re-index
    produces a clean slate.

    Parameters
    ----------
    repository_id:
        FK into the ``repositories`` table.
    clone_path:
        Absolute path to the cloned repository on disk.

    Returns
    -------
    A summary dict with counts useful for API responses and logging.
    """
    ensure_collection()

    # Clear stale vectors first (idempotent if none exist).
    deleted = delete_repository_points(repository_id)
    if deleted:
        logger.info("Cleared %s stale points before re-embedding repository_id=%s.", deleted, repository_id)

    # 1. Chunk
    chunk_result = chunk_repository(repository_id, clone_path)
    if not chunk_result.chunks:
        logger.info("No chunks produced for repository_id=%s — nothing to embed.", repository_id)
        return _summary(repository_id, chunk_result, vectors_stored=0)

    # 2. Embed in batches
    all_texts = [c.text for c in chunk_result.chunks]
    all_vectors: list[list[float]] = []

    for i in range(0, len(all_texts), EMBED_BATCH_SIZE):
        batch_texts = all_texts[i : i + EMBED_BATCH_SIZE]
        batch_vectors = embed_texts(batch_texts)
        all_vectors.extend(batch_vectors)

    # 3. Build payloads and upsert
    chunks_with_vectors: list[tuple[dict, list[float]]] = []
    for chunk, vector in zip(chunk_result.chunks, all_vectors):
        payload = {
            "repository_id": chunk.repository_id,
            "file_path": chunk.file_path,
            "language": chunk.language,
            "chunk_kind": chunk.kind,
            "symbol_name": chunk.symbol_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "text": chunk.text,
        }
        chunks_with_vectors.append((payload, vector))

    vectors_stored = upsert_chunks(chunks_with_vectors)

    logger.info(
        "Embedded repository_id=%s — chunks=%s vectors_stored=%s",
        repository_id,
        len(chunk_result.chunks),
        vectors_stored,
    )
    return _summary(repository_id, chunk_result, vectors_stored=vectors_stored)


def get_embedding_summary(repository_id: int) -> dict:
    """Return embedding stats for a repository (no chunking, just Qdrant count)."""
    vector_count = count_repository_points(repository_id)
    return {
        "repository_id": repository_id,
        "vector_count": vector_count,
    }


def _summary(repository_id: int, chunk_result, *, vectors_stored: int) -> dict:
    return {
        "repository_id": repository_id,
        "files_chunked": chunk_result.files_chunked,
        "symbol_chunks": chunk_result.symbol_chunk_count,
        "window_chunks": chunk_result.window_chunk_count,
        "total_chunks": len(chunk_result.chunks),
        "vectors_stored": vectors_stored,
    }
