"""Shared RAG chat execution used by direct chat and the Code Agent."""

from __future__ import annotations

from cache.semantic_cache import lookup_cached_chat, store_cached_chat
from config import settings
from rag.generator import generate_repository_answer
from rag.prompts import AgentProfile
from rag.retriever import retrieve_repository_context
from vector_store.embeddings import embed_texts
from vector_store.qdrant_store import RetrievedChunk


def chunk_to_source(chunk: RetrievedChunk, *, excerpt_limit: int = 500) -> dict:
    excerpt = chunk.text if len(chunk.text) <= excerpt_limit else f"{chunk.text[:excerpt_limit]}…"
    return {
        "file_path": chunk.file_path,
        "language": chunk.language,
        "chunk_kind": chunk.chunk_kind,
        "symbol_name": chunk.symbol_name,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "score": chunk.score,
        "excerpt": excerpt,
    }


def execute_rag_chat(
    repository_id: int,
    *,
    message: str,
    repository_full_name: str,
    top_k: int = 5,
    history: list[dict[str, str]] | None = None,
    use_hybrid: bool | None = None,
    use_semantic_cache: bool | None = None,
    agent_profile: AgentProfile = "code",
    retrieval_query: str | None = None,
    include_graph_context: bool | None = None,
    cache_route: str | None = None,
    cache_agent: str | None = None,
) -> dict:
    """Run semantic cache lookup, retrieval, generation, and optional cache store."""
    history = history or []
    cache_enabled = settings.semantic_cache_enabled if use_semantic_cache is None else use_semantic_cache
    can_lookup_cache = cache_enabled
    can_store_cache = cache_enabled
    steps: list[str] = []
    search_query = retrieval_query or message

    question_embedding: list[float] | None = None
    if can_lookup_cache:
        steps.append("cache_lookup")
        question_embedding = embed_texts([message])[0]
        cached = lookup_cached_chat(repository_id, message, question_embedding=question_embedding)
        if cached is not None:
            steps.append("cache_hit")
            return {
                "answer": cached.answer,
                "sources": cached.sources,
                "model": cached.model,
                "retrieval_mode": cached.retrieval_mode,
                "cache_hit": True,
                "cache_similarity": cached.similarity,
                "agent_steps": steps,
                "graph_context": [],
                "route": cached.route,
                "agent": cached.agent,
            }
        steps.append("cache_miss")

    steps.append("retrieve")
    chunks, retrieval_mode, _reranked = retrieve_repository_context(
        repository_id,
        search_query,
        top_k=top_k,
        use_hybrid=use_hybrid,
    )

    steps.append("generate")
    graph_blocks: list[str] = []
    use_graph = (
        include_graph_context
        if include_graph_context is not None
        else agent_profile == "architecture"
    )
    if use_graph and settings.graph_rag_enabled:
        from graph_rag.retriever import retrieve_graph_context

        graph_blocks = retrieve_graph_context(repository_id, message)
        if graph_blocks:
            steps.append("graph_context")

    answer, model = generate_repository_answer(
        question=message,
        repository_full_name=repository_full_name,
        chunks=chunks,
        history=history,
        agent_profile=agent_profile,
        extra_context_blocks=graph_blocks,
    )

    sources = [chunk_to_source(chunk) for chunk in chunks]
    if can_store_cache:
        store_cached_chat(
            repository_id,
            message,
            question_embedding=question_embedding,
            answer=answer,
            sources=sources,
            model=model,
            retrieval_mode=retrieval_mode,
            route=cache_route,
            agent=cache_agent,
        )
        steps.append("cache_store")

    return {
        "answer": answer,
        "sources": sources,
        "model": model,
        "retrieval_mode": retrieval_mode,
        "cache_hit": False,
        "cache_similarity": None,
        "agent_steps": steps,
        "graph_context": graph_blocks,
    }
