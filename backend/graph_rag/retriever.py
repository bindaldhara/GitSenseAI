"""Graph-augmented retrieval for architecture-style questions."""

from __future__ import annotations

import logging
import re

from graph_rag.store import get_edges_for_nodes, search_nodes

logger = logging.getLogger(__name__)


def _question_tokens(question: str) -> list[str]:
    tokens = [token.lower() for token in re.split(r"\W+", question) if len(token) >= 3]
    if not tokens:
        compact = question.strip().lower()
        if compact:
            tokens = [compact[:40]]
    return tokens[:6]


def _label_for_key(node_key: str, node_lookup: dict[str, dict]) -> str:
    node = node_lookup.get(node_key)
    if node is None:
        return node_key
    if node["node_type"] == "file":
        return node["file_path"] or node["label"]
    if node["node_type"] == "symbol":
        file_path = node.get("file_path") or ""
        return f"{file_path}:{node['label']}"
    return node["label"]


def retrieve_graph_context(repository_id: int, question: str, *, limit: int = 8) -> list[str]:
    """Return human-readable graph relationship blocks for LLM context."""
    tokens = _question_tokens(question)
    matched_nodes = search_nodes(repository_id, tokens, limit=limit)
    if not matched_nodes:
        return []

    node_lookup = {row["node_key"]: row for row in matched_nodes}
    node_keys = list(node_lookup.keys())
    edges = get_edges_for_nodes(repository_id, node_keys, limit=limit * 4)

    lines: list[str] = []
    for node in matched_nodes[:limit]:
        kind = node.get("symbol_kind") or node["node_type"]
        file_path = node.get("file_path") or "—"
        lines.append(f"Graph node [{kind}] {node['label']} in {file_path}")

    for edge in edges[:limit * 2]:
        source_label = _label_for_key(edge["source_key"], node_lookup)
        target_label = _label_for_key(edge["target_key"], node_lookup)
        lines.append(f"Graph edge: {source_label} --{edge['edge_type']}--> {target_label}")

    logger.info(
        "Graph context for repository_id=%s matched_nodes=%s edges=%s",
        repository_id,
        len(matched_nodes),
        len(edges),
    )
    return [f"[Graph context]\n{line}" for line in lines[:limit + 4]]
