"""Diagram intent detection — kept import-light to avoid circular dependencies."""

from __future__ import annotations

import re

_DIAGRAM_HINTS = re.compile(
    r"\b(diagram|mermaid|flowchart|chart|visualize|draw)\b",
    re.IGNORECASE,
)

_DEPENDENCY_HINTS = re.compile(
    r"\b(import|imports|dependency|dependencies|depend on|module map)\b",
    re.IGNORECASE,
)


def wants_diagram(message: str) -> bool:
    """True when the user is asking for a diagram visualization."""
    return bool(_DIAGRAM_HINTS.search(message))


def infer_diagram_type(message: str) -> str:
    """Infer dependency vs architecture diagram from the user message."""
    if _DEPENDENCY_HINTS.search(message):
        return "dependency"
    if _DIAGRAM_HINTS.search(message):
        return "architecture"
    return "architecture"
