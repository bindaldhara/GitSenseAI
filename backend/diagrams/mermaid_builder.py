"""Build Mermaid diagram source from repository graph import edges."""

from __future__ import annotations

import re

from graph_rag.store import list_import_dependencies

_INVALID_MERMAID_LABEL = re.compile(r"[{}<>#;\[\]|]")
_IMPORT_NOISE = re.compile(r"^\s*import\s*\{", re.IGNORECASE)
_MAX_DIAGRAM_EDGES = 14
_MAX_LABEL_LEN = 32


def _display_label(label: str) -> str:
    compact = label.strip().replace("\\", "/")
    if "/" in compact:
        parts = [part for part in compact.split("/") if part]
        if len(parts) >= 2:
            return "/".join(parts[-2:])
        return parts[-1]
    if len(compact) > _MAX_LABEL_LEN:
        return f"…{compact[-_MAX_LABEL_LEN + 1:]}"
    return compact


def _sanitize_label(label: str, *, max_len: int = _MAX_LABEL_LEN) -> str | None:
    compact = _display_label(label).replace('"', "'")
    if not compact or _IMPORT_NOISE.search(compact) or _INVALID_MERMAID_LABEL.search(compact):
        return None
    if len(compact) > max_len:
        compact = f"…{compact[-max_len + 1:]}"
    return compact


def _register_node(node_map: dict[str, str], label: str) -> str | None:
    safe = _sanitize_label(label)
    if not safe:
        return None
    if safe not in node_map:
        node_map[safe] = f"n{len(node_map) + 1}"
    return node_map[safe]


def _path_matches(source_file: str, path_filter: str) -> bool:
    file_norm = source_file.replace("\\", "/").lower()
    filter_norm = path_filter.replace("\\", "/").lower()
    if filter_norm in file_norm:
        return True
    file_base = file_norm.rsplit("/", 1)[-1]
    filter_base = filter_norm.rsplit("/", 1)[-1]
    return file_base == filter_base


def _build_flowchart(edges: list[tuple[str, str]]) -> str | None:
    node_map: dict[str, str] = {}
    edge_lines: list[str] = []
    seen_edges: set[str] = set()

    for source, target in edges[:_MAX_DIAGRAM_EDGES]:
        source_id = _register_node(node_map, source)
        target_id = _register_node(node_map, target)
        if not source_id or not target_id:
            continue
        edge = f"  {source_id} --> {target_id}"
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        edge_lines.append(edge)

    if not edge_lines:
        return None

    lines = ["flowchart TD"]
    for label, node_id in node_map.items():
        lines.append(f"  {node_id}[\"{label}\"]")
    lines.extend(edge_lines)
    return "\n".join(lines)


def infer_path_filter_from_question(message: str) -> str | None:
    """Extract a file or folder hint from the user question (optional focus)."""
    file_match = re.search(
        r"(?:[`'\"]?)(?:\./)?((?:[\w.-]+/)*[\w.-]+\.(?:jsx?|tsx?|vue))(?:[`'\"]?)",
        message,
        re.IGNORECASE,
    )
    if file_match:
        return file_match.group(1)

    lowered = message.lower()
    if "home" in lowered:
        return "Home"
    if "frontend" in lowered or "component" in lowered:
        return "components"
    if "backend" in lowered or "api" in lowered:
        return "api"
    return None


def build_import_mermaid(
    repository_id: int,
    *,
    path_filter: str | None = None,
    limit: int = 50,
) -> str | None:
    """Build a flowchart from file → module import edges (optionally filtered by path)."""
    rows = list_import_dependencies(
        repository_id,
        limit=limit,
        source_path_filter=path_filter,
    )
    edges: list[tuple[str, str]] = []

    for row in rows:
        source_file = row.get("source_file") or row.get("source_key") or ""
        target = row.get("target_label") or row.get("target_key") or ""
        if not source_file or not target:
            continue
        if path_filter and not _path_matches(source_file, path_filter):
            continue
        edges.append((source_file, target))

    return _build_flowchart(edges)
