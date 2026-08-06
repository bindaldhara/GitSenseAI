"""Graph RAG service helpers for API responses."""

from __future__ import annotations

from graph_rag.store import get_graph_counts, list_import_dependencies


def get_repository_graph_summary(repository_id: int) -> dict:
    counts = get_graph_counts(repository_id)
    return {
        "repository_id": repository_id,
        **counts,
    }


def get_repository_graph_dependencies(repository_id: int, *, limit: int = 100) -> dict:
    rows = list_import_dependencies(repository_id, limit=limit)
    dependencies = [
        {
            "source_file": row["source_file"] or row["source_key"],
            "target_label": row["target_label"] or row["target_key"],
            "target_type": row["target_type"] or "module",
            "edge_type": row["edge_type"],
        }
        for row in rows
    ]
    return {
        "repository_id": repository_id,
        "dependency_count": len(dependencies),
        "dependencies": dependencies,
        "limit": limit,
    }
