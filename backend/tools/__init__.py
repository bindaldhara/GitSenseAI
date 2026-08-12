"""MCP-compatible tools for repository operations (Day 15)."""

from tools.clone_repo import clone_repo
from tools.find_dead_code import find_dead_code
from tools.generate_docs import generate_docs
from tools.mcp_user import resolve_mcp_user_id
from tools.preflight import require_mcp_infrastructure

__all__ = [
    "clone_repo",
    "find_dead_code",
    "generate_docs",
    "require_mcp_infrastructure",
    "resolve_mcp_user_id",
]
