"""Retrieve relevant code chunks for a user question."""

from __future__ import annotations

from vector_store.embeddings import embed_texts
from vector_store.qdrant_store import RetrievedChunk, search_repository_chunks


def format_chunk_for_prompt(chunk: RetrievedChunk) -> str:
    """Render one retrieved chunk as a labeled context block."""
    location = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
    symbol = f" ({chunk.symbol_name})" if chunk.symbol_name else ""
    header = f"[{chunk.language} | {chunk.chunk_kind}{symbol} | {location}]"
    return f"{header}\n{chunk.text}"


def retrieve_repository_context(
    repository_id: int,
    question: str,
    *,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Embed the question and return the most similar indexed chunks."""
    query_vector = embed_texts([question])[0]
    return search_repository_chunks(
        repository_id,
        query_vector,
        top_k=top_k,
    )
