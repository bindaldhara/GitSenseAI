"""MCP tool: clone and index a public GitHub repository."""

from __future__ import annotations

from fastapi import HTTPException

from services.repository_service import create_repository_submission
from tools.errors import ToolError
from tools.preflight import require_mcp_infrastructure


def clone_repo(url: str, user_id: int | None = None) -> dict:
    """
    Clone a public GitHub repository, parse source files, and build search indexes.

    Returns repository metadata including id, full_name, and status when successful.
    """
    require_mcp_infrastructure()
    try:
        record = create_repository_submission(url, user_id=user_id)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise ToolError(detail) from exc
    except Exception as exc:
        raise ToolError(f"Clone failed: {exc}") from exc

    return {
        "ok": True,
        "repository_id": record["id"],
        "full_name": record["full_name"],
        "status": record["status"],
        "url": record["url"],
        "user_id": record.get("user_id"),
        "message": "Repository cloned, parsed, and indexed for chat and search.",
    }
