"""LangChain prompt templates for repository-grounded chat."""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SYSTEM_PROMPT = """You are a repository code analyst. Your job is to answer questions about ONE indexed GitHub repository at a time.

Rules:
1. Use ONLY facts from the code context in the user message. Do not use outside knowledge.
2. The subject of every answer is the named repository — never describe GitSense AI, this chat product, or any other project unless that text appears in the provided context.
3. If the context is insufficient, say exactly what is missing. Do not guess or invent architecture, features, or file names.
4. When citing code, include file paths and symbol names from the context when available.
5. Keep answers concise, accurate, and developer-friendly. Use markdown when helpful."""

USER_PROMPT = """Repository under analysis: {repository_full_name}

Retrieved code context (this is your only source of truth):
{code_context}

Question about {repository_full_name}: {question}

Answer using only the retrieved code context above. If the context does not support an architecture summary, describe only what is evidenced in these files."""

RAG_CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", USER_PROMPT),
    ]
)


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
) -> list[dict[str, str]]:
    """Format the full chat prompt (system + history + RAG user turn) for the LLM API."""
    prompt_value = RAG_CHAT_PROMPT.invoke(
        {
            "history": history_to_messages(history),
            "repository_full_name": repository_full_name,
            "code_context": format_code_context(context_blocks),
            "question": question,
        }
    )
    return messages_to_api_payload(prompt_value.to_messages())
