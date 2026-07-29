"""Cascade cleanup and re-index hooks for downstream stores.

These functions are called by delete/reindex flows in repository_service.py.
Qdrant hooks are now live (Day 5). Graph RAG remains a stub.
"""

from __future__ import annotations

import logging

from vector_store.ingest import embed_repository
from vector_store.qdrant_store import delete_repository_points

logger = logging.getLogger(__name__)


def cleanup_qdrant_for_repository(repository_id: int, full_name: str) -> None:
    """Remove all vector points for a repository from Qdrant."""
    deleted = delete_repository_points(repository_id)
    logger.info(
        "Qdrant cleanup: deleted %s points for repository_id=%s full_name=%s",
        deleted,
        repository_id,
        full_name,
    )


def cleanup_graph_for_repository(repository_id: int, full_name: str) -> None:
    """Remove graph nodes/edges for a repository when Graph RAG exists."""
    logger.info(
        "Graph cleanup hook skipped (not implemented yet) for repository_id=%s full_name=%s",
        repository_id,
        full_name,
    )


def reembed_repository(repository_id: int, full_name: str, clone_path: str) -> dict:
    """Run the full chunking → embedding → Qdrant upsert pipeline."""
    logger.info(
        "Starting embedding pipeline for repository_id=%s full_name=%s",
        repository_id,
        full_name,
    )
    return embed_repository(repository_id, clone_path)
