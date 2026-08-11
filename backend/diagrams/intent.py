"""Diagram intent detection — kept import-light to avoid circular dependencies."""

from __future__ import annotations

import re

_DIAGRAM_HINTS = re.compile(
    r"\b(diagram|mermaid|flowchart|chart|visualize|draw)\b",
    re.IGNORECASE,
)


def wants_diagram(message: str) -> bool:
    """True when the user is asking for a diagram visualization."""
    return bool(_DIAGRAM_HINTS.search(message))
