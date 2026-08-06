"""Build a repository knowledge graph from parsed symbols."""

from __future__ import annotations

import logging
import re

from db import db_cursor
from graph_rag.models import GraphEdge, GraphNode
from graph_rag.store import clear_repository_graph, insert_graph

logger = logging.getLogger(__name__)

_FILE_PREFIX = "file:"
_SYMBOL_PREFIX = "symbol:"
_MODULE_PREFIX = "module:"


def _file_key(file_path: str) -> str:
    return f"{_FILE_PREFIX}{file_path}"


def _symbol_key(file_path: str, name: str, start_line: int) -> str:
    return f"{_SYMBOL_PREFIX}{file_path}:{name}:{start_line}"


def _module_key(module_name: str) -> str:
    normalized = re.sub(r"\s+", " ", module_name.strip().lower())
    return f"{_MODULE_PREFIX}{normalized}"


def _extract_module_target(import_text: str) -> str:
    compact = " ".join(import_text.split())
    match = re.search(r"(?:from|import)\s+([A-Za-z0-9_.]+)", compact)
    if match:
        return match.group(1)
    return compact[:120]


def build_repository_graph(repository_id: int) -> dict:
    """Build file/symbol/module nodes and dependency edges from Postgres parse data."""
    clear_repository_graph(repository_id)

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, path, language
            FROM repository_files
            WHERE repository_id = %s
            ORDER BY path
            """,
            (repository_id,),
        )
        files = list(cursor.fetchall())

        cursor.execute(
            """
            SELECT
                s.name,
                s.kind,
                s.start_line,
                s.end_line,
                s.parent_name,
                f.path AS file_path
            FROM repository_symbols s
            JOIN repository_files f ON f.id = s.file_id
            WHERE s.repository_id = %s
            ORDER BY f.path, s.start_line
            """,
            (repository_id,),
        )
        symbols = list(cursor.fetchall())

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for file_row in files:
        file_path = file_row["path"]
        nodes.append(
            GraphNode(
                node_key=_file_key(file_path),
                node_type="file",
                label=file_path,
                file_path=file_path,
                metadata={"language": file_row["language"]},
            )
        )

    symbol_nodes_by_file: dict[str, list[tuple[str, str, str, int, str | None]]] = {}
    for symbol in symbols:
        file_path = symbol["file_path"]
        symbol_key = _symbol_key(file_path, symbol["name"], symbol["start_line"])
        if symbol["kind"] == "import":
            module_label = _extract_module_target(symbol["name"])
            module_key = _module_key(module_label)
            nodes.append(
                GraphNode(
                    node_key=module_key,
                    node_type="module",
                    label=module_label,
                    metadata={"import_statement": symbol["name"]},
                )
            )
            edges.append(
                GraphEdge(
                    source_key=_file_key(file_path),
                    target_key=module_key,
                    edge_type="imports",
                    metadata={"line": symbol["start_line"]},
                )
            )
            continue

        nodes.append(
            GraphNode(
                node_key=symbol_key,
                node_type="symbol",
                label=symbol["name"],
                file_path=file_path,
                symbol_kind=symbol["kind"],
                metadata={
                    "start_line": symbol["start_line"],
                    "end_line": symbol["end_line"],
                    "parent_name": symbol["parent_name"],
                },
            )
        )
        edges.append(
            GraphEdge(
                source_key=_file_key(file_path),
                target_key=symbol_key,
                edge_type="defines",
            )
        )
        symbol_nodes_by_file.setdefault(file_path, []).append(
            (symbol_key, symbol["name"], symbol["kind"], symbol["start_line"], symbol["parent_name"])
        )

    for file_path, file_symbols in symbol_nodes_by_file.items():
        class_like = {
            name: key
            for key, name, kind, _start, _parent in file_symbols
            if kind in {"class", "type"}
        }
        for symbol_key, name, _kind, start_line, parent_name in file_symbols:
            if not parent_name:
                continue
            parent_key = class_like.get(parent_name)
            if parent_key and parent_key != symbol_key:
                edges.append(
                    GraphEdge(
                        source_key=parent_key,
                        target_key=symbol_key,
                        edge_type="contains",
                    )
                )

    insert_graph(repository_id, nodes, edges)
    logger.info(
        "Built graph for repository_id=%s nodes=%s edges=%s",
        repository_id,
        len(nodes),
        len(edges),
    )
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "files": len(files),
        "symbols": len(symbols),
    }
