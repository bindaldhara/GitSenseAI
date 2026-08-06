"""Repository diagram generation service."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from config import settings
from diagrams.generator import generate_architecture_mermaid
from diagrams.intent import infer_diagram_type
from diagrams.mermaid_builder import (
    build_file_import_mermaid,
    build_filtered_import_mermaid,
    build_import_dependency_mermaid,
    build_local_import_mermaid,
    infer_path_filter_from_question,
)
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
    diagram_type: str = "auto",
    limit: int = 50,
) -> dict:
    """Generate a Mermaid diagram for a repository (dependency graph or architecture)."""
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

    resolved_type = diagram_type if diagram_type != "auto" else infer_diagram_type(message)
    sources: list[dict] = []
    model = ""
    title = "Architecture diagram"
    description = ""

    if resolved_type == "dependency":
        if not embedding_summary.get("graph_ready"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Knowledge graph not built. Reindex with GRAPH_RAG_ENABLED=true.",
            )
        mermaid = build_import_dependency_mermaid(repository_id, limit=limit)
        if not mermaid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No import edges found in the knowledge graph for this repository.",
            )
        title = "File import dependencies"
        description = "Built from knowledge-graph import edges (file → module)."
    else:
        mermaid = None
        path_filter = infer_path_filter_from_question(message)

        if embedding_summary.get("graph_ready"):
            if path_filter:
                file_mermaid = build_file_import_mermaid(repository_id, file_hint=path_filter)
                if file_mermaid:
                    mermaid = file_mermaid
                    title = "File import map"
                    description = f"Imports for `{path_filter}` from the knowledge graph."

            if not mermaid:
                filtered = build_filtered_import_mermaid(
                    repository_id,
                    path_filter=path_filter,
                    limit=limit + 30,
                )
                if filtered:
                    mermaid = filtered
                    title = "Component import map"
                    description = (
                        "Built from import edges in the knowledge graph"
                        + (f" (filtered: `{path_filter}`)." if path_filter else ".")
                    )

            if not mermaid:
                local = build_local_import_mermaid(
                    repository_id,
                    path_filter=path_filter,
                    limit=limit,
                )
                if local:
                    mermaid = local
                    title = "Local component wiring"
                    description = (
                        "Local import paths only"
                        + (f" (filtered: `{path_filter}`)." if path_filter else ".")
                    )

        if not mermaid:
            graph_blocks: list[str] = []
            if settings.graph_rag_enabled and embedding_summary.get("graph_ready"):
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

        if not mermaid and embedding_summary.get("graph_ready"):
            mermaid = build_import_dependency_mermaid(repository_id, limit=limit)
            if mermaid:
                title = "File import dependencies"
                description = "Fallback: all import edges from the knowledge graph."

        if not mermaid or not is_publishable_mermaid(mermaid):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Could not build a valid Mermaid diagram. Reindex the repository "
                    "with GRAPH_RAG_ENABLED=true and try a path-specific question."
                ),
            )

    logger.info(
        "Generated %s mermaid diagram for repository_id=%s (%s chars).",
        resolved_type,
        repository_id,
        len(mermaid),
    )

    return {
        "repository_id": repository_id,
        "question": message,
        "diagram_type": "dependency" if resolved_type == "dependency" else "architecture",
        "title": title,
        "description": description,
        "mermaid": mermaid,
        "model": model,
        "sources": sources,
    }
