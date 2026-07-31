"""Retrieval Lab — compare vector-only vs hybrid + rerank (no LLM)."""

from __future__ import annotations

import time

from fastapi import HTTPException, status

from rag.retriever import retrieve_repository_context
from schemas.retrieval_lab import RetrievalModeResult
from services.chat_service import _to_source
from services.repository_service import get_repository_by_id
from vector_store import get_embedding_summary

LAB_RETRIEVAL_MODES = [
    {
        "mode_id": "vector",
        "label": "Vector only",
        "use_hybrid": False,
        "use_rerank": False,
    },
    {
        "mode_id": "hybrid_rerank",
        "label": "Hybrid + cross-encoder",
        "use_hybrid": True,
        "use_rerank": True,
    },
]


def compare_retrieval_modes(
    repository_id: int,
    *,
    message: str,
    top_k: int = 5,
) -> dict:
    """Compare vector-only retrieval against hybrid search with cross-encoder reranking."""
    repository = get_repository_by_id(repository_id)

    if repository["status"] != "cloned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Repository is not ready for retrieval (status={repository['status']}). "
                "Wait for indexing to finish or reindex the repository."
            ),
        )

    embedding_summary = get_embedding_summary(repository_id)
    if embedding_summary["vector_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository has no indexed vectors. Reindex the repository before comparing retrieval.",
        )

    results: list[RetrievalModeResult] = []
    for mode in LAB_RETRIEVAL_MODES:
        started = time.perf_counter()
        chunks, retrieval_mode, _reranked = retrieve_repository_context(
            repository_id,
            message,
            top_k=top_k,
            use_hybrid=mode["use_hybrid"],
            use_rerank=mode["use_rerank"],
        )
        retrieval_ms = round((time.perf_counter() - started) * 1000, 1)

        results.append(
            RetrievalModeResult(
                mode_id=mode["mode_id"],
                label=mode["label"],
                retrieval_mode=retrieval_mode,
                retrieval_ms=retrieval_ms,
                sources=[_to_source(chunk) for chunk in chunks],
            )
        )

    return {
        "repository_id": repository_id,
        "question": message,
        "top_k": top_k,
        "results": results,
    }
