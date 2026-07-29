"""Prompt templates for repository-grounded chat."""

SYSTEM_PROMPT = """You are GitSense AI, a software intelligence assistant.
Answer questions about the indexed repository using ONLY the provided code context.
If the context does not contain enough information, say so clearly instead of guessing.
When referencing code, mention file paths and symbol names when available.
Keep answers concise, accurate, and developer-friendly. Use markdown when helpful."""


def build_user_prompt(
    question: str,
    repository_full_name: str,
    context_blocks: list[str],
) -> str:
    """Combine retrieved chunks and the user question into one prompt."""
    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(no relevant code found)"
    return (
        f"Repository: {repository_full_name}\n\n"
        f"Code context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer based on the code context above."
    )
