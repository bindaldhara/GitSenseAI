"""Orchestrate retrieval and response generation for repository chat."""

from __future__ import annotations

from fastapi import HTTPException, status

from agents.graph import run_agent_chat
from config import settings
from cache.semantic_cache import lookup_cached_chat
from diagrams.intent import wants_diagram
from rag.chat_pipeline import execute_rag_chat
from services.repository_service import get_repository_by_id
from vector_store import get_embedding_summary
from vector_store.embeddings import embed_texts


def _validate_repository_ready(repository_id: int, user_id: int | None = None) -> dict:
    repository = get_repository_by_id(repository_id, user_id=user_id)

    if repository["status"] != "cloned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Repository is not ready for chat (status={repository['status']}). "
                "Wait for indexing to finish or reindex the repository."
            ),
        )

    embedding_summary = get_embedding_summary(repository_id)
    if embedding_summary["vector_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository has no indexed vectors. Reindex the repository before chatting.",
        )
    return repository


def chat_with_repository(
    repository_id: int,
    *,
    message: str,
    top_k: int = 5,
    history: list[dict[str, str]] | None = None,
    use_hybrid: bool | None = None,
    use_semantic_cache: bool | None = None,
    use_agents: bool | None = None,
    user_id: int | None = None,
) -> dict:
    """Answer a question about an indexed repository using agents or direct RAG."""
    repository = _validate_repository_ready(repository_id, user_id=user_id)
    history = history or []
    agents_enabled = settings.agents_enabled if use_agents is None else use_agents
    cache_enabled = settings.semantic_cache_enabled if use_semantic_cache is None else use_semantic_cache

    if cache_enabled and not wants_diagram(message):
        question_embedding = embed_texts([message])[0]
        cached = lookup_cached_chat(repository_id, message, question_embedding=question_embedding)
        if cached is not None:
            return {
                "repository_id": repository_id,
                "answer": cached.answer,
                "sources": cached.sources,
                "model": cached.model,
                "retrieval_mode": cached.retrieval_mode,
                "cache_hit": True,
                "cache_similarity": cached.similarity,
                "route": cached.route or ("code" if agents_enabled else None),
                "agent": cached.agent or ("code" if agents_enabled else None),
                "agent_steps": ["cache_hit"],
            }

    if agents_enabled:
        return run_agent_chat(
            repository_id,
            message=message,
            repository_full_name=repository["full_name"],
            top_k=top_k,
            history=history,
            use_hybrid=use_hybrid,
            use_semantic_cache=use_semantic_cache,
        )

    result = execute_rag_chat(
        repository_id,
        message=message,
        repository_full_name=repository["full_name"],
        top_k=top_k,
        history=history,
        use_hybrid=use_hybrid,
        use_semantic_cache=use_semantic_cache,
    )
    return {
        "repository_id": repository_id,
        **result,
    }
