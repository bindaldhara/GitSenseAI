"""LangGraph agent state for repository chat."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

AgentRoute = Literal["code", "documentation", "architecture"]
AgentName = Literal["code", "documentation", "architecture"]


class AgentState(TypedDict, total=False):
    repository_id: int
    repository_full_name: str
    message: str
    top_k: int
    history: list[dict[str, str]]
    use_hybrid: bool | None
    use_semantic_cache: bool | None
    route: AgentRoute
    agent: AgentName
    answer: str
    sources: list[dict[str, Any]]
    model: str
    retrieval_mode: Literal["hybrid", "vector"]
    cache_hit: bool
    cache_similarity: float | None
    agent_steps: list[str]
