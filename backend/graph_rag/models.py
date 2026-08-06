"""Graph node and edge dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GraphNode:
    node_key: str
    node_type: str
    label: str
    file_path: str | None = None
    symbol_kind: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source_key: str
    target_key: str
    edge_type: str
    metadata: dict = field(default_factory=dict)
