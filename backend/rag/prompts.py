"""LangChain prompt templates for repository-grounded chat."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

AgentProfile = Literal["code", "documentation", "architecture"]

SYSTEM_PROMPT = """You are a repository code analyst. Your job is to answer questions about ONE indexed GitHub repository at a time.

Rules:
1. Use ONLY facts from the code context in the user message. Do not use outside knowledge.
2. The subject of every answer is the named repository — never describe GitSense AI, this chat product, or any other project unless that text appears in the provided context.
3. If the context is insufficient, say exactly what is missing. Do not guess or invent architecture, features, or file names.
4. When citing code, include file paths and symbol names from the context when available.
5. Keep answers concise, accurate, and developer-friendly. Use markdown when helpful."""

DOCUMENTATION_SYSTEM_PROMPT = """You are a technical documentation specialist for a single GitHub repository.

Rules:
1. Use ONLY facts from the retrieved repository context. Do not invent features, endpoints, or setup steps.
2. Focus on developer-facing documentation: README content, setup/install, configuration, usage, and API surface evidenced in the code.
3. Prefer citing markdown files (README, docs/), config examples, and public entry points when they appear in context.
4. If asked to draft documentation, structure output clearly with markdown headings and bullet lists grounded in the retrieved files.
5. If the context lacks enough detail, state what files or areas are missing instead of guessing."""

ARCHITECTURE_SYSTEM_PROMPT = """You are a software architecture analyst for a single GitHub repository.

Rules:
1. Use ONLY facts from the retrieved repository context. Do not invent services, databases, or deployment topology.
2. Explain high-level structure: main modules, entry points, how major components interact, and key dependencies visible in the code.
3. When helpful, use markdown sections (Overview, Main components, Data flow, Entry points). Optional mermaid diagrams only when supported by retrieved context.
4. Distinguish what is directly evidenced in the repo from what is unknown.
5. Keep the explanation practical for a developer onboarding to this codebase."""

USER_PROMPT = """Repository under analysis: {repository_full_name}

Retrieved code context (this is your only source of truth):
{code_context}

Question about {repository_full_name}: {question}

Answer using only the retrieved code context above. If the context does not support an architecture summary, describe only what is evidenced in these files."""

DOCUMENTATION_USER_PROMPT = """Repository under analysis: {repository_full_name}

Retrieved repository context (this is your only source of truth):
{code_context}

Documentation question about {repository_full_name}: {question}

Answer using only the retrieved context above. When drafting docs, base every section on files and symbols present in the context."""

ARCHITECTURE_USER_PROMPT = """Repository under analysis: {repository_full_name}

Retrieved repository context (this is your only source of truth):
{code_context}

Architecture question about {repository_full_name}: {question}

Answer using only the retrieved context above. Describe structure and relationships evidenced in these files."""

_AGENT_PROMPTS: dict[AgentProfile, ChatPromptTemplate] = {
    "code": ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", USER_PROMPT),
        ]
    ),
    "documentation": ChatPromptTemplate.from_messages(
        [
            ("system", DOCUMENTATION_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", DOCUMENTATION_USER_PROMPT),
        ]
    ),
    "architecture": ChatPromptTemplate.from_messages(
        [
            ("system", ARCHITECTURE_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", ARCHITECTURE_USER_PROMPT),
        ]
    ),
}


def format_code_context(context_blocks: list[str]) -> str:
    """Join retrieved chunk blocks into one context string for the prompt."""
    if not context_blocks:
        return "(no relevant code found)"
    return "\n\n---\n\n".join(context_blocks)


def history_to_messages(history: list[dict[str, str]] | None) -> list[BaseMessage]:
    """Convert API chat history into LangChain message objects."""
    messages: list[BaseMessage] = []
    for item in history or []:
        role = item.get("role", "")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def messages_to_api_payload(messages: list[BaseMessage]) -> list[dict[str, str]]:
    """Convert LangChain messages to OpenAI/Ollama chat API format."""
    payload: list[dict[str, str]] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            payload.append({"role": "system", "content": message.content})
        elif isinstance(message, HumanMessage):
            payload.append({"role": "user", "content": message.content})
        elif isinstance(message, AIMessage):
            payload.append({"role": "assistant", "content": message.content})
    return payload


def build_chat_messages(
    *,
    question: str,
    repository_full_name: str,
    context_blocks: list[str],
    history: list[dict[str, str]] | None = None,
    agent_profile: AgentProfile = "code",
) -> list[dict[str, str]]:
    """Format the full chat prompt (system + history + RAG user turn) for the LLM API."""
    prompt_template = _AGENT_PROMPTS[agent_profile]
    prompt_value = prompt_template.invoke(
        {
            "history": history_to_messages(history),
            "repository_full_name": repository_full_name,
            "code_context": format_code_context(context_blocks),
            "question": question,
        }
    )
    return messages_to_api_payload(prompt_value.to_messages())


# Backward-compatible alias used by older imports.
RAG_CHAT_PROMPT = _AGENT_PROMPTS["code"]
