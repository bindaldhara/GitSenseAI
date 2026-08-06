"""LangGraph workflow: Router → Code | Documentation | Architecture Agent."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from langgraph.graph import END, START, StateGraph

from agents.architecture_agent import architecture_agent_node
from agents.code_agent import code_agent_node
from agents.documentation_agent import documentation_agent_node
from agents.router import router_node
from agents.state import AgentRoute, AgentState

logger = logging.getLogger(__name__)

AgentNodeName = Literal["code_agent", "documentation_agent", "architecture_agent"]


def _route_after_router(state: AgentState) -> AgentNodeName:
    route: AgentRoute = state.get("route", "code")
    if route == "documentation":
        return "documentation_agent"
    if route == "architecture":
        return "architecture_agent"
    return "code_agent"


@lru_cache(maxsize=1)
def _compiled_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("code_agent", code_agent_node)
    graph.add_node("documentation_agent", documentation_agent_node)
    graph.add_node("architecture_agent", architecture_agent_node)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "code_agent": "code_agent",
            "documentation_agent": "documentation_agent",
            "architecture_agent": "architecture_agent",
        },
    )
    graph.add_edge("code_agent", END)
    graph.add_edge("documentation_agent", END)
    graph.add_edge("architecture_agent", END)
    return graph.compile()


def run_agent_chat(
    repository_id: int,
    *,
    message: str,
    repository_full_name: str,
    top_k: int = 5,
    history: list[dict[str, str]] | None = None,
    use_hybrid: bool | None = None,
    use_semantic_cache: bool | None = None,
) -> dict:
    """Execute the LangGraph agent workflow and return a chat API payload."""
    initial_state: AgentState = {
        "repository_id": repository_id,
        "repository_full_name": repository_full_name,
        "message": message,
        "top_k": top_k,
        "history": history or [],
        "use_hybrid": use_hybrid,
        "use_semantic_cache": use_semantic_cache,
        "agent_steps": [],
        "retrieval_mode": "vector",
        "cache_hit": False,
        "sources": [],
    }

    final_state = _compiled_graph().invoke(initial_state)
    logger.info(
        "Agent chat completed repository_id=%s route=%s agent=%s steps=%s",
        repository_id,
        final_state.get("route"),
        final_state.get("agent"),
        final_state.get("agent_steps"),
    )

    return {
        "repository_id": repository_id,
        "answer": final_state.get("answer", ""),
        "sources": final_state.get("sources") or [],
        "model": final_state.get("model", ""),
        "retrieval_mode": final_state.get("retrieval_mode", "vector"),
        "cache_hit": bool(final_state.get("cache_hit")),
        "cache_similarity": final_state.get("cache_similarity"),
        "route": final_state.get("route"),
        "agent": final_state.get("agent"),
        "agent_steps": final_state.get("agent_steps") or [],
    }
