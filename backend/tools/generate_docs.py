"""MCP tool: generate repository documentation via the documentation RAG agent."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException

from rag.chat_pipeline import execute_rag_chat
from services.repository_service import get_repository_by_full_name
from tools.errors import ToolError
from tools.preflight import require_mcp_infrastructure

DocKind = Literal["readme", "api", "onboarding"]

_DOC_PROMPTS: dict[DocKind, str] = {
    "readme": (
        "Draft a README.md for this repository. Include: project overview, prerequisites, "
        "installation/setup, how to run locally, configuration, and main entry points. "
        "Use markdown headings. Only include facts from the retrieved context."
    ),
    "api": (
        "Document the API surface evidenced in this repository: routes, handlers, request/response "
        "shapes, and how clients call them. Use markdown. Only include facts from retrieved context."
    ),
    "onboarding": (
        "Write an onboarding guide for a new developer: architecture snapshot, where to start reading, "
        "key modules, and common workflows. Use markdown. Only include facts from retrieved context."
    ),
}


def generate_docs(
    repo_name: str,
    *,
    doc_kind: DocKind = "readme",
    user_id: int | None = None,
) -> dict:
    """Generate markdown documentation grounded in indexed repository context."""
    require_mcp_infrastructure()
    try:
        record = get_repository_by_full_name(repo_name, user_id=user_id)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise ToolError(detail) from exc

    if record["status"] != "cloned":
        raise ToolError(
            f"Repository {record['full_name']} is not ready (status={record['status']}). "
            "Clone and index the repository first."
        )

    repository_id = record["id"]
    prompt = _DOC_PROMPTS.get(doc_kind, _DOC_PROMPTS["readme"])
    result = execute_rag_chat(
        repository_id,
        message=prompt,
        repository_full_name=record["full_name"],
        top_k=12,
        agent_profile="documentation",
        retrieval_query=f"README documentation setup API docs markdown: {prompt}",
        use_semantic_cache=False,
    )

    return {
        "ok": True,
        "repository_id": repository_id,
        "full_name": record["full_name"],
        "doc_kind": doc_kind,
        "markdown": result["answer"],
        "model": result["model"],
        "retrieval_mode": result["retrieval_mode"],
        "source_count": len(result.get("sources") or []),
    }
