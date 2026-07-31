"""LLM response generation for repository chat."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status
from openai import OpenAI

from config import settings
from rag.prompts import build_chat_messages
from rag.retriever import format_chunk_for_prompt
from vector_store.qdrant_store import RetrievedChunk

logger = logging.getLogger(__name__)


def _format_context_blocks(chunks: list[RetrievedChunk]) -> list[str]:
    return [format_chunk_for_prompt(chunk) for chunk in chunks]


def _generate_with_openai(
    *,
    question: str,
    repository_full_name: str,
    context_blocks: list[str],
    history: list[dict[str, str]],
) -> str:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured.",
        )

    client = OpenAI(api_key=settings.openai_api_key)
    messages = build_chat_messages(
        question=question,
        repository_full_name=repository_full_name,
        context_blocks=context_blocks,
        history=history,
    )

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM returned an empty response.",
        )
    return content.strip()


def _generate_with_ollama(
    *,
    question: str,
    repository_full_name: str,
    context_blocks: list[str],
    history: list[dict[str, str]],
) -> str:
    messages = build_chat_messages(
        question=question,
        repository_full_name=repository_full_name,
        context_blocks=context_blocks,
        history=history,
    )

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Ollama request failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is unavailable. Start Ollama or switch LLM_PROVIDER to openai.",
        ) from exc

    data = response.json()
    content = data.get("message", {}).get("content")
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an empty response.",
        )
    return content.strip()


def generate_repository_answer(
    *,
    question: str,
    repository_full_name: str,
    chunks: list[RetrievedChunk],
    history: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Generate an answer grounded in retrieved chunks.

    Returns ``(answer, model_name)``.
    """
    context_blocks = _format_context_blocks(chunks)
    conversation_history = history or []

    if settings.llm_provider == "ollama":
        answer = _generate_with_ollama(
            question=question,
            repository_full_name=repository_full_name,
            context_blocks=context_blocks,
            history=conversation_history,
        )
        return answer, settings.ollama_model

    answer = _generate_with_openai(
        question=question,
        repository_full_name=repository_full_name,
        context_blocks=context_blocks,
        history=conversation_history,
    )
    return answer, settings.openai_model
