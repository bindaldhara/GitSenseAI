"""Code Agent — repository-grounded Q&A via the existing RAG pipeline."""

from __future__ import annotations

from agents.rag_agent import run_specialist_rag
from agents.state import AgentState


def code_agent_node(state: AgentState) -> AgentState:
    """LangGraph node: run cache → retrieve → generate for code questions."""
    return run_specialist_rag(state, agent="code")
