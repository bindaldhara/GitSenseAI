"""MCP tool: clone and index a public GitHub repository."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from services.repository_service import (
    create_repository_submission,
    get_repository_by_full_name,
    parse_github_repository_url,
    reindex_repository,
    resolve_repository_clone_path,
)
from tools.errors import ToolError
from tools.preflight import require_mcp_infrastructure


def clone_repo(url: str, user_id: int | None = None, *, force_reindex: bool = False) -> dict:
    """
    Clone a public GitHub repository, parse source files, and build search indexes.

    If the repository is already registered but the local clone is missing or failed,
    this re-indexes automatically instead of returning a conflict error.
    """
    require_mcp_infrastructure()
    repository = parse_github_repository_url(url)

    try:
        existing = get_repository_by_full_name(repository.full_name, user_id=user_id)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            raise ToolError(detail) from exc
        existing = None

    if existing is not None:
        return _ensure_indexed(existing, force_reindex=force_reindex)

    try:
        record = create_repository_submission(url, user_id=user_id)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise ToolError(detail) from exc
    except Exception as exc:
        raise ToolError(f"Clone failed: {exc}") from exc

    return _success(record, action="cloned")


def _ensure_indexed(record: dict, *, force_reindex: bool) -> dict:
    clone_path = resolve_repository_clone_path(record["clone_path"])
    clone_missing = not clone_path.is_dir()
    needs_reindex = force_reindex or clone_missing or record["status"] != "cloned"

    if not needs_reindex:
        return _success(record, action="already_indexed")

    try:
        updated = reindex_repository(record["id"])
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise ToolError(detail) from exc
    except Exception as exc:
        raise ToolError(f"Re-index failed: {exc}") from exc

    payload = _success(updated, action="reindexed")
    payload["clone_was_missing"] = clone_missing
    return payload


def _success(record: dict, *, action: str) -> dict:
    messages = {
        "cloned": "Repository cloned, parsed, and indexed for chat and search.",
        "reindexed": "Repository re-cloned, parsed, and indexed.",
        "already_indexed": "Repository is already indexed. Pass force_reindex=true to refresh.",
    }
    return {
        "ok": True,
        "action": action,
        "repository_id": record["id"],
        "full_name": record["full_name"],
        "status": record["status"],
        "url": record["url"],
        "user_id": record.get("user_id"),
        "message": messages[action],
    }
