"""Graph RAG lab — compare traditional RAG vs graph-augmented answers."""

from __future__ import annotations

import time

from fastapi import HTTPException, status

from rag.chat_pipeline import execute_rag_chat
from services.repository_service import get_repository_by_id
from vector_store import get_embedding_summary

GRAPH_RAG_COMPARE_MODES = [
    {
        "mode_id": "traditional_rag",
        "label": "Traditional RAG",
        "description": "Hybrid vector + BM25 retrieval, then LLM — no graph relationships.",
        "include_graph_context": False,
    },
    {
        "mode_id": "graph_rag",
        "label": "Graph RAG",
        "description": "Same retrieval plus knowledge-graph nodes/edges injected into the prompt.",
        "include_graph_context": True,
    },
]


def compare_graph_rag_modes(
    repository_id: int,
    *,
    message: str,
    top_k: int = 5,
) -> dict:
    """Run the same architecture question with and without graph context."""
    repository = get_repository_by_id(repository_id)

    if repository["status"] != "cloned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Repository is not ready for comparison (status={repository['status']}). "
                "Wait for indexing to finish or reindex the repository."
            ),
        )

    embedding_summary = get_embedding_summary(repository_id)
    if embedding_summary["vector_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository has no indexed vectors. Reindex before comparing Graph RAG.",
        )

    if not embedding_summary["graph_ready"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Repository has no knowledge graph. Reindex with GRAPH_RAG_ENABLED=true "
                "before comparing Graph RAG."
            ),
        )

    results: list[dict] = []
    for mode in GRAPH_RAG_COMPARE_MODES:
        started = time.perf_counter()
        payload = execute_rag_chat(
            repository_id,
            message=message,
            repository_full_name=repository["full_name"],
            top_k=top_k,
            use_semantic_cache=False,
            agent_profile="architecture",
            include_graph_context=mode["include_graph_context"],
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

        graph_context = payload.get("graph_context") or []
        results.append(
            {
                "mode_id": mode["mode_id"],
                "label": mode["label"],
                "description": mode["description"],
                "answer": payload["answer"],
                "model": payload["model"],
                "retrieval_mode": payload["retrieval_mode"],
                "sources": payload["sources"],
                "graph_context": graph_context,
                "graph_context_count": len(graph_context),
                "elapsed_ms": elapsed_ms,
            }
        )

    return {
        "repository_id": repository_id,
        "question": message,
        "top_k": top_k,
        "graph_node_count": embedding_summary["graph_node_count"],
        "graph_edge_count": embedding_summary["graph_edge_count"],
        "results": results,
    }
