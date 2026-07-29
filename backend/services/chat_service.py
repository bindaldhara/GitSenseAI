"""Orchestrate retrieval and response generation for repository chat."""

from __future__ import annotations

from fastapi import HTTPException, status

from rag.generator import generate_repository_answer
from rag.retriever import retrieve_repository_context
from services.repository_service import get_repository_by_id
from vector_store import get_embedding_summary
from vector_store.qdrant_store import RetrievedChunk


def _to_source(chunk: RetrievedChunk, *, excerpt_limit: int = 500) -> dict:
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


def chat_with_repository(
    repository_id: int,
    *,
    message: str,
    top_k: int = 5,
    history: list[dict[str, str]] | None = None,
) -> dict:
    """Answer a question about an indexed repository using RAG."""
    repository = get_repository_by_id(repository_id)

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

    chunks = retrieve_repository_context(repository_id, message, top_k=top_k)
    answer, model = generate_repository_answer(
        question=message,
        repository_full_name=repository["full_name"],
        chunks=chunks,
        history=history,
    )

    return {
        "repository_id": repository_id,
        "answer": answer,
        "sources": [_to_source(chunk) for chunk in chunks],
        "model": model,
    }
