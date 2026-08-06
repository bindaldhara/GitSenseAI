from pydantic import BaseModel, Field


class GraphSummaryResponse(BaseModel):
    repository_id: int
    node_count: int
    edge_count: int
    nodes_by_type: dict[str, int]
    edges_by_type: dict[str, int]
    graph_ready: bool


class GraphDependencyRow(BaseModel):
    source_file: str
    target_label: str
    target_type: str
    edge_type: str


class GraphDependenciesResponse(BaseModel):
    repository_id: int
    dependency_count: int
    dependencies: list[GraphDependencyRow]
    limit: int
