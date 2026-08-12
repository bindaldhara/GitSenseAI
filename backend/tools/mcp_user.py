"""Map MCP tool calls to app user rows (no Supabase JWT on stdio MCP)."""

from __future__ import annotations

from services.user_service import get_user_id_by_email
from tools.errors import ToolError


def resolve_mcp_user_id(owner_email: str | None) -> int | None:
    """
    Resolve GitSense app user id for an MCP tool call.

    MCP runs outside the browser — there is no Supabase session on the wire.
    Pass owner_email (same as Supabase login) to attach repos and enforce access.
    Omit owner_email to create/use public repos (user_id IS NULL).
    """
    if owner_email is None or not owner_email.strip():
        return None

    user_id = get_user_id_by_email(owner_email)
    if user_id is None:
        raise ToolError(
            f"No GitSense user for '{owner_email.strip()}'. "
            "Sign in or register once in the web app so the user row exists."
        )
    return user_id
