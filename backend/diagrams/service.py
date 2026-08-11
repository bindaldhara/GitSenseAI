"""Repository diagram generation service."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from config import settings
from diagrams.generator import generate_architecture_mermaid
from diagrams.mermaid_builder import build_import_mermaid, infer_path_filter_from_question
from diagrams.validate import is_publishable_mermaid
from graph_rag.retriever import retrieve_graph_context
from rag.chat_pipeline import chunk_to_source
from services.repository_service import get_repository_by_id
from vector_store import get_embedding_summary

logger = logging.getLogger(__name__)


def generate_repository_diagram(
    repository_id: int,
    *,
    message: str,
    limit: int = 50,
) -> dict:
    """Generate a Mermaid import flowchart for a repository."""
    repository = get_repository_by_id(repository_id)

    if repository["status"] != "cloned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is not ready (status={repository['status']}).",
        )

    embedding_summary = get_embedding_summary(repository_id)
    if embedding_summary["vector_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository has no indexed vectors. Reindex before generating diagrams.",
        )

    if not embedding_summary.get("graph_ready"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Knowledge graph not built. Reindex with GRAPH_RAG_ENABLED=true.",
        )

    path_filter = infer_path_filter_from_question(message)
    sources: list[dict] = []
    model = ""
    mermaid: str | None = None
    title = "File import dependencies"
    description = "Built from knowledge-graph import edges (file → module)."

    if path_filter:
        mermaid = build_import_mermaid(repository_id, path_filter=path_filter, limit=limit)
        if mermaid:
            title = "Import map"
            description = f"Import edges for paths matching `{path_filter}`."

    if not mermaid:
        mermaid = build_import_mermaid(repository_id, limit=limit)
        if path_filter and mermaid:
            description = (
                f"No focused import map for `{path_filter}`; showing repository import edges."
            )

    if not mermaid:
        graph_blocks: list[str] = []
        if settings.graph_rag_enabled:
            graph_blocks = retrieve_graph_context(repository_id, message)

        candidate, chunks, model = generate_architecture_mermaid(
            repository_id=repository_id,
            repository_full_name=repository["full_name"],
            question=message,
            extra_context_blocks=graph_blocks,
        )
        if candidate and is_publishable_mermaid(candidate):
            mermaid = candidate
            sources = [chunk_to_source(chunk) for chunk in chunks]
            title = "Architecture diagram"
            description = "Generated from hybrid retrieval + LLM."

    if not mermaid or not is_publishable_mermaid(mermaid):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not build a valid Mermaid diagram. Reindex with GRAPH_RAG_ENABLED=true "
                "or ask about a specific file path (e.g. src/components/Home/Home.js)."
            ),
        )

    logger.info(
        "Generated import mermaid diagram for repository_id=%s (%s chars).",
        repository_id,
        len(mermaid),
    )

    return {
        "repository_id": repository_id,
        "question": message,
        "title": title,
        "description": description,
        "mermaid": mermaid,
        "model": model,
        "sources": sources,
    }
