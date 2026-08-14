"""MCP tool: ask a natural-language question about an indexed repository."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException

from config import settings
from rag.chat_pipeline import execute_rag_chat
from rag.prompts import AgentProfile
from services.chat_service import chat_with_repository
from services.repository_service import get_repository_by_full_name
from tools.errors import ToolError
from tools.preflight import require_mcp_infrastructure
from vector_store import get_embedding_summary

AskAgent = Literal["auto", "code", "docs", "architecture"]

_AGENT_PROFILES: dict[str, AgentProfile] = {
    "code": "code",
    "docs": "documentation",
    "architecture": "architecture",
}


def ask_repo(
    repo_name: str,
    question: str,
    *,
    agent: AskAgent = "auto",
    top_k: int = 8,
    user_id: int | None = None,
) -> dict:
    """Answer a question about a cloned, indexed repository using hybrid RAG."""
    require_mcp_infrastructure()

    cleaned_question = question.strip()
    if not cleaned_question:
        raise ToolError("question is required.")

    if not 1 <= top_k <= 20:
        raise ToolError("top_k must be between 1 and 20.")

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
    embedding_summary = get_embedding_summary(repository_id)
    if embedding_summary["vector_count"] == 0:
        raise ToolError(
            f"Repository {record['full_name']} has no indexed vectors. "
            "Run clone_repo to index it before asking questions."
        )

    if agent == "auto":
        try:
            result = chat_with_repository(
                repository_id,
                message=cleaned_question,
                top_k=top_k,
                user_id=user_id,
                use_semantic_cache=False,
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            raise ToolError(detail) from exc
    else:
        profile = _AGENT_PROFILES[agent]
        result = execute_rag_chat(
            repository_id,
            message=cleaned_question,
            repository_full_name=record["full_name"],
            top_k=top_k,
            agent_profile=profile,
            use_semantic_cache=False,
            include_graph_context=profile == "architecture" and settings.graph_rag_enabled,
        )

    return {
        "ok": True,
        "repository_id": repository_id,
        "full_name": record["full_name"],
        "question": cleaned_question,
        "agent": result.get("agent") or agent,
        "route": result.get("route"),
        "answer": result.get("answer", ""),
        "sources": result.get("sources") or [],
        "model": result.get("model", ""),
        "retrieval_mode": result.get("retrieval_mode", "vector"),
        "source_count": len(result.get("sources") or []),
        "cache_hit": bool(result.get("cache_hit")),
    }
