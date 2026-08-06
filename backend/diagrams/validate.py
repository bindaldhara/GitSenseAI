"""Validate and normalize Mermaid diagram source."""

from __future__ import annotations

import re

_MERMAID_FENCE_RE = re.compile(r"```mermaid\s*([\s\S]*?)```", re.IGNORECASE)
_VALID_START_RE = re.compile(r"^(flowchart|graph)\s", re.IGNORECASE)
_MERMAID_LINE_RE = re.compile(
    r"^(flowchart|graph|subgraph|end|classDef|class|linkStyle|style)\s",
    re.IGNORECASE,
)
_EDGE_RE = re.compile(r"--+>|---|-.->|==>")
_NODE_DEF_RE = re.compile(r"^\s*n\d+\s*\[")
_PUBLISHABLE_NODE_RE = re.compile(r"^n\d+\[")
_PUBLISHABLE_EDGE_RE = re.compile(r"^n\d+\s*-->\s*n\d+")
_PROSE_LINE_RE = re.compile(
    r"^(okay|let's|the |this |here|note|flowchart:|#|\*\*|\[start\])",
    re.IGNORECASE,
)


def extract_mermaid_block(text: str) -> str:
    match = _MERMAID_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def is_valid_mermaid(text: str) -> bool:
    """Return True when text looks like parseable Mermaid flowchart syntax."""
    if not text or not text.strip():
        return False

    stripped = text.strip()
    if not _VALID_START_RE.match(stripped):
        return False

    has_structure = False
    for line in stripped.splitlines():
        compact = line.strip()
        if not compact:
            continue
        if _PROSE_LINE_RE.match(compact):
            return False
        if (
            _MERMAID_LINE_RE.match(compact)
            or _EDGE_RE.search(compact)
            or _NODE_DEF_RE.match(compact)
            or "-->" in compact
        ):
            has_structure = True

    return has_structure


def is_publishable_mermaid(text: str) -> bool:
    """True when Mermaid uses the canonical n1[\"label\"] format produced by the graph builder."""
    if not is_valid_mermaid(text):
        return False

    saw_content = False
    for line in text.splitlines():
        compact = line.strip()
        if not compact:
            continue
        saw_content = True
        if compact.startswith("flowchart"):
            continue
        if _PUBLISHABLE_NODE_RE.match(compact) or _PUBLISHABLE_EDGE_RE.match(compact):
            continue
        return False

    return saw_content


def normalize_mermaid(text: str) -> str | None:
    """Extract and keep only lines that look like valid Mermaid flowchart syntax."""
    raw = extract_mermaid_block(text)
    if not raw:
        return None

    kept: list[str] = []
    for line in raw.splitlines():
        compact = line.strip()
        if not compact:
            continue
        if _PROSE_LINE_RE.match(compact):
            continue
        if (
            _VALID_START_RE.match(compact)
            or _MERMAID_LINE_RE.match(compact)
            or _EDGE_RE.search(compact)
            or _NODE_DEF_RE.match(compact)
            or compact == "end"
        ):
            kept.append(line.rstrip())

    if not kept:
        return None

    result = "\n".join(kept)
    return result if is_publishable_mermaid(result) else None
