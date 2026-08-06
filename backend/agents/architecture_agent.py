"""Architecture Agent — high-level structure and component relationships."""

from __future__ import annotations

from agents.rag_agent import run_specialist_rag
from agents.state import AgentState


def architecture_agent_node(state: AgentState) -> AgentState:
    """LangGraph node for architecture-focused questions."""
    return run_specialist_rag(state, agent="architecture")
