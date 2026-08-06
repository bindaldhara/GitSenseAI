"""Persist repository knowledge graphs in PostgreSQL."""

from __future__ import annotations

import json
import logging

from db import db_cursor
from graph_rag.models import GraphEdge, GraphNode

logger = logging.getLogger(__name__)


def clear_repository_graph(repository_id: int) -> int:
    """Delete all graph nodes and edges for a repository."""
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM repository_graph_edges WHERE repository_id = %s",
            (repository_id,),
        )
        cursor.execute(
            "DELETE FROM repository_graph_nodes WHERE repository_id = %s",
            (repository_id,),
        )
        removed = cursor.rowcount
    logger.info("Cleared graph data for repository_id=%s.", repository_id)
    return removed


def insert_graph(repository_id: int, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
    """Bulk insert nodes and edges for a repository."""
    with db_cursor(commit=True) as cursor:
        for node in nodes:
            cursor.execute(
                """
                INSERT INTO repository_graph_nodes (
                    repository_id, node_key, node_type, label, file_path, symbol_kind, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (repository_id, node_key) DO UPDATE SET
                    node_type = EXCLUDED.node_type,
                    label = EXCLUDED.label,
                    file_path = EXCLUDED.file_path,
                    symbol_kind = EXCLUDED.symbol_kind,
                    metadata = EXCLUDED.metadata
                """,
                (
                    repository_id,
                    node.node_key,
                    node.node_type,
                    node.label,
                    node.file_path,
                    node.symbol_kind,
                    json.dumps(node.metadata),
                ),
            )

        for edge in edges:
            cursor.execute(
                """
                INSERT INTO repository_graph_edges (
                    repository_id, source_key, target_key, edge_type, metadata
                ) VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (repository_id, source_key, target_key, edge_type) DO NOTHING
                """,
                (
                    repository_id,
                    edge.source_key,
                    edge.target_key,
                    edge.edge_type,
                    json.dumps(edge.metadata),
                ),
            )


def get_graph_counts(repository_id: int) -> dict:
    """Return node/edge totals and grouped counts."""
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS count FROM repository_graph_nodes WHERE repository_id = %s",
            (repository_id,),
        )
        node_count = int(cursor.fetchone()["count"])

        cursor.execute(
            "SELECT COUNT(*) AS count FROM repository_graph_edges WHERE repository_id = %s",
            (repository_id,),
        )
        edge_count = int(cursor.fetchone()["count"])

        cursor.execute(
            """
            SELECT node_type, COUNT(*) AS count
            FROM repository_graph_nodes
            WHERE repository_id = %s
            GROUP BY node_type
            ORDER BY node_type
            """,
            (repository_id,),
        )
        nodes_by_type = {row["node_type"]: int(row["count"]) for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT edge_type, COUNT(*) AS count
            FROM repository_graph_edges
            WHERE repository_id = %s
            GROUP BY edge_type
            ORDER BY edge_type
            """,
            (repository_id,),
        )
        edges_by_type = {row["edge_type"]: int(row["count"]) for row in cursor.fetchall()}

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "nodes_by_type": nodes_by_type,
        "edges_by_type": edges_by_type,
        "graph_ready": node_count > 0,
    }


def list_import_dependencies(
    repository_id: int,
    *,
    limit: int = 100,
    source_path_filter: str | None = None,
) -> list[dict]:
    """Return file → module import edges for dependency mapping."""
    params: list = [repository_id]
    path_clause = ""
    if source_path_filter:
        normalized = source_path_filter.replace("\\", "/")
        basename = normalized.rsplit("/", 1)[-1]
        path_clause = " AND (src.file_path ILIKE %s OR src.file_path ILIKE %s)"
        params.extend([f"%{normalized}%", f"%{basename}%"])

    params.append(limit)

    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                e.source_key,
                e.target_key,
                e.edge_type,
                src.file_path AS source_file,
                tgt.label AS target_label,
                tgt.node_type AS target_type
            FROM repository_graph_edges e
            LEFT JOIN repository_graph_nodes src
                ON src.repository_id = e.repository_id AND src.node_key = e.source_key
            LEFT JOIN repository_graph_nodes tgt
                ON tgt.repository_id = e.repository_id AND tgt.node_key = e.target_key
            WHERE e.repository_id = %s AND e.edge_type = 'imports'{path_clause}
            ORDER BY src.file_path NULLS LAST, tgt.label
            LIMIT %s
            """,
            params,
        )
        return list(cursor.fetchall())


def search_nodes(repository_id: int, tokens: list[str], *, limit: int = 20) -> list[dict]:
    """Find graph nodes whose label or file path matches any token."""
    if not tokens:
        return []

    clauses = []
    params: list = [repository_id]
    for token in tokens[:6]:
        clauses.append("(label ILIKE %s OR file_path ILIKE %s OR node_key ILIKE %s)")
        pattern = f"%{token}%"
        params.extend([pattern, pattern, pattern])

    where_match = " OR ".join(clauses)
    params.append(limit)

    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT node_key, node_type, label, file_path, symbol_kind
            FROM repository_graph_nodes
            WHERE repository_id = %s AND ({where_match})
            ORDER BY
                CASE node_type
                    WHEN 'file' THEN 1
                    WHEN 'symbol' THEN 2
                    ELSE 3
                END,
                file_path NULLS LAST,
                label
            LIMIT %s
            """,
            params,
        )
        return list(cursor.fetchall())


def get_edges_for_nodes(repository_id: int, node_keys: list[str], *, limit: int = 40) -> list[dict]:
    """Return edges touching any of the given node keys."""
    if not node_keys:
        return []

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT source_key, target_key, edge_type
            FROM repository_graph_edges
            WHERE repository_id = %s
              AND (source_key = ANY(%s) OR target_key = ANY(%s))
            LIMIT %s
            """,
            (repository_id, node_keys, node_keys, limit),
        )
        return list(cursor.fetchall())
