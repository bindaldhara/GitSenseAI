"""Prompt templates for repository-grounded chat."""

SYSTEM_PROMPT = """You are a repository code analyst. Your job is to answer questions about ONE indexed GitHub repository at a time.

Rules:
1. Use ONLY facts from the code context in the user message. Do not use outside knowledge.
2. The subject of every answer is the named repository — never describe GitSense AI, this chat product, or any other project unless that text appears in the provided context.
3. If the context is insufficient, say exactly what is missing. Do not guess or invent architecture, features, or file names.
4. When citing code, include file paths and symbol names from the context when available.
5. Keep answers concise, accurate, and developer-friendly. Use markdown when helpful."""


def build_user_prompt(
    question: str,
    repository_full_name: str,
    context_blocks: list[str],
) -> str:
    """Combine retrieved chunks and the user question into one prompt."""
    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no relevant code found)"
    return (
        f"Repository under analysis: {repository_full_name}\n\n"
        f"Retrieved code context (this is your only source of truth):\n{context}\n\n"
        f"Question about {repository_full_name}: {question}\n\n"
        "Answer using only the retrieved code context above. "
        "If the context does not support an architecture summary, describe only what is evidenced in these files."
    )
