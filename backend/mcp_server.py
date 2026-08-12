"""
GitSense AI MCP server (Day 15).

Exposes clone_repo, generate_docs, and run_tests for Cursor, Claude Desktop, and Codex.

User scoping: MCP has no Supabase JWT. Pass optional owner_email (GitSense login email)
to attach repos to that user; omit for public repos (visible to all logged-in users).

Run from repo root (loads .env automatically):
    cd backend && python mcp_server.py

Or: make mcp-server
"""

from __future__ import annotations

import json
import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from db import initialize_database
from tools.clone_repo import clone_repo as clone_repo_tool
from tools.errors import ToolError
from tools.generate_docs import generate_docs as generate_docs_tool
from tools.mcp_user import resolve_mcp_user_id
from vector_store.qdrant_store import ensure_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("GitSense AI")


def _json_result(payload: dict) -> str:
    return json.dumps(payload, indent=2, default=str)


def _tool_response(payload: dict) -> str:
    if payload.get("ok"):
        return _json_result(payload)
    return _json_result({"ok": False, "error": payload.get("error", "Tool failed.")})


@mcp.tool()
def clone_repo(url: str, owner_email: str | None = None) -> str:
    """Clone a public GitHub repo, parse it, and index it. Optional owner_email scopes the repo to that GitSense user."""
    try:
        user_id = resolve_mcp_user_id(owner_email)
        return _json_result(clone_repo_tool(url, user_id=user_id))
    except ToolError as exc:
        return _tool_response({"ok": False, "error": exc.message})


@mcp.tool()
def generate_docs(
    repo_name: str,
    doc_kind: Literal["readme", "api", "onboarding"] = "readme",
    owner_email: str | None = None,
) -> str:
    """Generate and return Markdown documentation for a cloned repo.

    The successful response is the document content itself, ready to save as
    README.md (or another .md file). repo_name is owner/repo (for example,
    octocat/Hello-World) or a GitHub URL. Pass owner_email if the repo is
    user-owned.
    """
    try:
        user_id = resolve_mcp_user_id(owner_email)
        result = generate_docs_tool(repo_name, doc_kind=doc_kind, user_id=user_id)
        return result["markdown"]
    except ToolError as exc:
        return _tool_response({"ok": False, "error": exc.message})

def _bootstrap() -> None:
    logger.info("Initializing database and Qdrant collection for MCP tools…")
    try:
        from tools.preflight import require_mcp_infrastructure

        require_mcp_infrastructure()
        initialize_database()
        ensure_collection()
        logger.info("GitSense MCP server ready (postgres, redis, qdrant OK).")
    except ToolError as exc:
        logger.error("%s", exc.message)
        logger.error(
            "MCP server will start, but tools will fail until you run: make docker-up"
        )
    except Exception as exc:
        logger.error("Bootstrap failed: %s", exc)
        logger.error("Start infrastructure: make docker-up")


if __name__ == "__main__":
    _bootstrap()
    mcp.run()
