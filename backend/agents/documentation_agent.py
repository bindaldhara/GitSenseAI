"""Documentation Agent — README, setup, and usage questions."""

from __future__ import annotations

from agents.rag_agent import run_specialist_rag
from agents.state import AgentState


def documentation_agent_node(state: AgentState) -> AgentState:
    """LangGraph node for documentation-focused questions."""
    return run_specialist_rag(state, agent="documentation")
