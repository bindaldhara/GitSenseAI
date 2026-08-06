"""Router Agent — classifies user intent before delegating to a specialist agent."""

from __future__ import annotations

import logging

from agents.llm import invoke_llm_text
from agents.state import AgentRoute, AgentState

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """You are a routing classifier for a codebase Q&A product.
Classify the user question into exactly ONE category:

- code: how the code works, where something is defined, implementation details, APIs, bugs, files, functions, tests
- documentation: writing or improving README, user guides, API docs, tutorials, markdown documentation
- architecture: high-level system design, service map, dependencies between components, infrastructure, diagrams

Reply with ONLY one lowercase word: code, documentation, or architecture. No punctuation or explanation."""

_VALID_ROUTES: set[str] = {"code", "documentation", "architecture"}


def _parse_route(raw: str) -> AgentRoute:
    normalized = raw.strip().lower().split()[0] if raw.strip() else "code"
    normalized = normalized.strip(".,;:\"'")
    if normalized in _VALID_ROUTES:
        return normalized  # type: ignore[return-value]
    logger.warning("Router returned unexpected value %r — defaulting to code.", raw)
    return "code"


def classify_route(question: str) -> AgentRoute:
    """Use the LLM to pick code, documentation, or architecture."""
    raw = invoke_llm_text(
        system=ROUTER_SYSTEM_PROMPT,
        user=f"Question: {question}",
        temperature=0.0,
    )
    return _parse_route(raw)


def router_node(state: AgentState) -> AgentState:
    """LangGraph node: set ``route`` and append a router step."""
    route = classify_route(state["message"])
    steps = list(state.get("agent_steps") or [])
    steps.append(f"router:{route}")
    logger.info("Router classified question as route=%s for repository_id=%s.", route, state["repository_id"])
    return {**state, "route": route, "agent_steps": steps}
