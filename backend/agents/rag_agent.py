"""Shared RAG execution helpers for specialist agents."""

from __future__ import annotations

import logging

from agents.state import AgentName, AgentState
from rag.chat_pipeline import execute_rag_chat

logger = logging.getLogger(__name__)

_AGENT_TOP_K_BOOST: dict[AgentName, int] = {
    "code": 0,
    "documentation": 3,
    "architecture": 5,
}

_RETRIEVAL_QUERY_PREFIX: dict[AgentName, str] = {
    "code": "",
    "documentation": "README documentation markdown setup usage guide API docs: ",
    "architecture": "architecture modules services components entry point structure dependencies: ",
}


def run_specialist_rag(state: AgentState, *, agent: AgentName) -> AgentState:
    """Run retrieval + generation with agent-specific prompts and retrieval tuning."""
    base_top_k = state.get("top_k", 5)
    effective_top_k = min(base_top_k + _AGENT_TOP_K_BOOST[agent], 20)
    retrieval_query = f"{_RETRIEVAL_QUERY_PREFIX[agent]}{state['message']}"

    result = execute_rag_chat(
        state["repository_id"],
        message=state["message"],
        repository_full_name=state["repository_full_name"],
        top_k=effective_top_k,
        history=state.get("history") or [],
        use_hybrid=state.get("use_hybrid"),
        use_semantic_cache=state.get("use_semantic_cache"),
        agent_profile=agent,
        retrieval_query=retrieval_query,
    )
    steps = list(state.get("agent_steps") or [])
    steps.append(f"agent:{agent}")
    steps.extend(result.get("agent_steps") or [])

    logger.info(
        "%s Agent completed for repository_id=%s (cache_hit=%s, top_k=%s).",
        agent.title(),
        state["repository_id"],
        result.get("cache_hit"),
        effective_top_k,
    )
    return {
        **state,
        "agent": agent,
        "answer": result["answer"],
        "sources": result["sources"],
        "model": result["model"],
        "retrieval_mode": result["retrieval_mode"],
        "cache_hit": result["cache_hit"],
        "cache_similarity": result.get("cache_similarity"),
        "agent_steps": steps,
    }
