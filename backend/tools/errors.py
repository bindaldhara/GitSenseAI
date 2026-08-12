"""Shared errors for MCP-compatible tools."""

from __future__ import annotations


class ToolError(Exception):
    """Raised when a tool cannot complete; message is safe to return to MCP clients."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
