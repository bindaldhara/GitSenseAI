"""Retrieve relevant code chunks for a user question."""

from __future__ import annotations

from rag.langchain_hybrid import RetrievalMode, retrieve_repository_context
from vector_store.qdrant_store import RetrievedChunk

__all__ = ["RetrievalMode", "format_chunk_for_prompt", "retrieve_repository_context"]


def format_chunk_for_prompt(chunk: RetrievedChunk) -> str:
    """Render one retrieved chunk as a labeled context block."""
    location = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
    symbol = f" ({chunk.symbol_name})" if chunk.symbol_name else ""
    header = f"[{chunk.language} | {chunk.chunk_kind}{symbol} | {location}]"
    return f"{header}\n{chunk.text}"
