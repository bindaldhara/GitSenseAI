"""Search code chunks across multiple repositories."""

from __future__ import annotations

from rag.chat_pipeline import chunk_to_source
from rag.retriever import retrieve_repository_context
from services.repository_service import list_repositories
from vector_store import get_embedding_summary


def search_across_repositories(
    query: str,
    *,
    user_id: int | None = None,
    repository_ids: list[int] | None = None,
    top_k: int = 5,
    use_hybrid: bool | None = None,
) -> dict:
    """Run hybrid/vector retrieval per repository and return grouped hits."""
    repositories = list_repositories(user_id=user_id)
    if repository_ids is not None:
        allowed = set(repository_ids)
        repositories = [repo for repo in repositories if repo["id"] in allowed]

    results: list[dict] = []
    for repository in repositories:
        if repository["status"] != "cloned":
            continue

        summary = get_embedding_summary(repository["id"])
        if summary["vector_count"] == 0:
            continue

        chunks, retrieval_mode, _reranked = retrieve_repository_context(
            repository["id"],
            query,
            top_k=top_k,
            use_hybrid=use_hybrid,
        )
        if not chunks:
            continue

        results.append(
            {
                "repository_id": repository["id"],
                "full_name": repository["full_name"],
                "retrieval_mode": retrieval_mode,
                "hits": [chunk_to_source(chunk) for chunk in chunks],
            }
        )

    return {
        "query": query,
        "repository_count": len(results),
        "results": results,
    }
