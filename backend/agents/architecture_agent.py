"""Architecture Agent — high-level structure, diagrams, and component relationships."""

from __future__ import annotations

import logging

from agents.rag_agent import run_specialist_rag
from agents.state import AgentState
from config import settings
from diagrams.intent import wants_diagram
from diagrams.service import generate_repository_diagram
from diagrams.validate import is_publishable_mermaid
from rag.chat_pipeline import chunk_to_source

logger = logging.getLogger(__name__)


def _format_diagram_answer(payload: dict) -> str:
    mermaid = payload.get("mermaid") or ""
    body = (
        f"### {payload['title']}\n\n"
        f"{payload['description']}\n\n"
    )
    if mermaid and is_publishable_mermaid(mermaid):
        body = (
            f"### {payload['title']}\n\n"
            f"{payload['description']}\n\n"
            f"```mermaid\n{mermaid}\n```\n\n"
            "_Click the image to see fully_"
        )
        return body
    return (
        f"{body}A diagram could not be rendered from the current graph data. "
        "Try re-indexing the repository or ask about a specific file path "
        "(e.g. `src/components/Home/Home.js` imports)."
    )


def architecture_agent_node(state: AgentState) -> AgentState:
    """LangGraph node for architecture-focused questions and Mermaid diagrams."""
    if wants_diagram(state["message"]):
        try:
            payload = generate_repository_diagram(
                state["repository_id"],
                message=state["message"],
            )
        except Exception:
            logger.warning(
                "Diagram generation failed for repository_id=%s.",
                state["repository_id"],
                exc_info=True,
            )
            steps = list(state.get("agent_steps") or [])
            steps.append("agent:architecture")
            steps.append("diagram_failed")
            return {
                **state,
                "agent": "architecture",
                "answer": (
                    "### Diagram unavailable\n\n"
                    "Could not build a valid Mermaid flowchart. "
                    "Re-index the repository with `GRAPH_RAG_ENABLED=true`, then ask about "
                    "a specific area (e.g. *imports used in `src/components/Home/Home.js`*)."
                ),
                "sources": [],
                "model": settings.ollama_model if settings.llm_provider == "ollama" else settings.openai_model,
                "retrieval_mode": "hybrid",
                "cache_hit": False,
                "agent_steps": steps,
            }

        steps = list(state.get("agent_steps") or [])
        steps.append("agent:architecture")
        steps.append("diagram_generate")

        model = payload.get("model") or (
            settings.ollama_model if settings.llm_provider == "ollama" else settings.openai_model
        )

        return {
            **state,
            "agent": "architecture",
            "answer": _format_diagram_answer(payload),
            "sources": payload.get("sources") or [],
            "model": model,
            "retrieval_mode": "hybrid",
            "cache_hit": False,
            "cache_similarity": None,
            "agent_steps": steps,
        }

    return run_specialist_rag(state, agent="architecture")
