"""Cascade cleanup and re-index hooks for downstream stores.

Qdrant and Graph RAG are not wired yet. These functions are the extension
points so delete/reindex can call real cleanup later without changing routes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def cleanup_qdrant_for_repository(repository_id: int, full_name: str) -> None:
    """Remove vector points for a repository when Qdrant ingestion exists."""
    logger.info(
        "Qdrant cleanup hook skipped (not implemented yet) for repository_id=%s full_name=%s",
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


def reembed_repository(repository_id: int, full_name: str, clone_path: str) -> None:
    """Re-run chunking/embeddings/Qdrant upsert when the indexing pipeline exists."""
    logger.info(
        "Re-embed hook skipped (not implemented yet) for repository_id=%s full_name=%s clone_path=%s",
        repository_id,
        full_name,
        clone_path,
    )
