"""
GitSense AI MCP server (Day 15).

Exposes ask_repo, clone_repo, generate_docs, and find_dead_code for Cursor, Claude Desktop, and Codex.

User scoping: MCP has no Supabase JWT. Pass optional owner_email (GitSense login email)
to attach repos to that user; omit for public repos (visible to all logged-in users).

Run from repo root (loads .env automatically):
    cd backend && python mcp_server.py

Or: make mcp-server
"""

from __future__ import annotations

import json
import logging
import os
from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from db import initialize_database
from tools.ask_repo import ask_repo as ask_repo_tool
from tools.clone_repo import clone_repo as clone_repo_tool
from tools.errors import ToolError
from tools.find_dead_code import find_dead_code as find_dead_code_tool
from tools.generate_docs import generate_docs as generate_docs_tool
from tools.mcp_user import resolve_mcp_user_id
from vector_store.qdrant_store import ensure_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _transport_security() -> TransportSecuritySettings:
    hosts = os.getenv(
        "MCP_ALLOWED_HOSTS",
        "api.gitsense.dharabindal.com,localhost,127.0.0.1",
    )
    origins = os.getenv(
        "MCP_ALLOWED_ORIGINS",
        "https://gitsense.dharabindal.com,https://api.gitsense.dharabindal.com",
    )
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[host.strip() for host in hosts.split(",") if host.strip()],
        allowed_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )


mcp = FastMCP(
    "GitSense AI",
    streamable_http_path="/",
    transport_security=_transport_security(),
)


def _json_result(payload: dict) -> str:
    return json.dumps(payload, indent=2, default=str)


def _tool_response(payload: dict) -> str:
    if payload.get("ok"):
        return _json_result(payload)
    return _json_result({"ok": False, "error": payload.get("error", "Tool failed.")})


@mcp.tool()
def ask_repo(
    repo_name: str,
    question: str,
    agent: Literal["auto", "code", "docs", "architecture"] = "auto",
    owner_email: str | None = None,
    top_k: int = 8,
) -> str:
    """Ask a natural-language question about an indexed repository.

    Uses hybrid search and RAG over the full codebase. Returns a grounded answer
    with source citations (file paths and line ranges). repo_name is owner/repo or
    a GitHub URL. agent: auto (router), code, docs, or architecture. Pass
    owner_email if the repository is user-owned.
    """
    try:
        user_id = resolve_mcp_user_id(owner_email)
        return _json_result(
            ask_repo_tool(
                repo_name,
                question,
                agent=agent,
                top_k=top_k,
                user_id=user_id,
            )
        )
    except ToolError as exc:
        return _tool_response({"ok": False, "error": exc.message})


@mcp.tool()
def clone_repo(
    url: str,
    owner_email: str | None = None,
    force_reindex: bool = False,
) -> str:
    """Clone a public GitHub repo, parse it, and index it.

    If the repo is already registered but the local clone is missing, it is
    re-indexed automatically. Set force_reindex=true to refresh an existing clone.
    Optional owner_email scopes the repo to that GitSense user.
    """
    try:
        user_id = resolve_mcp_user_id(owner_email)
        return _json_result(clone_repo_tool(url, user_id=user_id, force_reindex=force_reindex))
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


@mcp.tool()
def find_dead_code(
    repo_name: str,
    owner_email: str | None = None,
    max_results: int = 100,
) -> str:
    """Find likely-unused functions, classes, and types in a cloned repository.

    Results are static-analysis candidates only: review framework hooks, public
    APIs, reflection, and configuration before deleting anything. repo_name is
    owner/repo or a GitHub URL. Pass owner_email if the repository is user-owned.
    """
    try:
        user_id = resolve_mcp_user_id(owner_email)
        return _json_result(
            find_dead_code_tool(
                repo_name,
                user_id=user_id,
                max_results=max_results,
            )
        )
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


def get_mcp_http_app():
    """ASGI app for Streamable HTTP MCP at /mcp when mounted on FastAPI."""
    return mcp.streamable_http_app()


if __name__ == "__main__":
    _bootstrap()
    mcp.run()
