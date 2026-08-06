"""LLM-backed Mermaid diagram generation from retrieved repository context."""

from __future__ import annotations

import logging

from agents.llm import invoke_llm_text
from config import settings
from diagrams.validate import normalize_mermaid
from rag.prompts import format_code_context
from rag.retriever import retrieve_repository_context
from vector_store.qdrant_store import RetrievedChunk

logger = logging.getLogger(__name__)

_MERMAID_SYSTEM_PROMPT = """You generate Mermaid flowcharts for a software repository.

Output rules (strict):
- First line MUST be: flowchart TB
- Use only node definitions like: n1["src/path/file.js"]
- Use only edges like: n1 --> n2
- Maximum 12 nodes
- NO prose, NO markdown fences, NO explanations, NO numbered lists
- ONLY output valid Mermaid lines"""


def generate_architecture_mermaid(
    *,
    repository_id: int,
    repository_full_name: str,
    question: str,
    extra_context_blocks: list[str] | None = None,
    top_k: int = 10,
) -> tuple[str | None, list[RetrievedChunk], str]:
    """Retrieve context and ask the LLM for Mermaid-only output (validated)."""
    retrieval_query = f"Home page components imports structure: {question}"
    chunks, _mode, _reranked = retrieve_repository_context(
        repository_id,
        retrieval_query,
        top_k=top_k,
        use_hybrid=True,
        use_rerank=True,
    )

    from rag.retriever import format_chunk_for_prompt

    context_blocks = list(extra_context_blocks or [])
    context_blocks.extend(format_chunk_for_prompt(c) for c in chunks)
    context_text = format_code_context(context_blocks)

    raw = invoke_llm_text(
        system=_MERMAID_SYSTEM_PROMPT,
        user=(
            f"Repository: {repository_full_name}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Build a flowchart for: {question}"
        ),
        temperature=0.0,
    )

    mermaid = normalize_mermaid(raw)
    model = settings.ollama_model if settings.llm_provider == "ollama" else settings.openai_model

    if mermaid is None:
        logger.warning(
            "LLM returned invalid mermaid for repository_id=%s (len=%s).",
            repository_id,
            len(raw),
        )

    return mermaid, chunks, model
