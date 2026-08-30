"""Small LLM helper for agent routing (not RAG generation)."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from config import settings
from openai_client import openai_chat_client

logger = logging.getLogger(__name__)


def invoke_llm_text(*, system: str, user: str, temperature: float = 0.0) -> str:
    """Return a single short text completion from the configured LLM provider."""
    if settings.llm_provider == "ollama":
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Ollama router request failed.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama is unavailable. Start Ollama or switch LLM_PROVIDER to openai.",
            ) from exc
        content = response.json().get("message", {}).get("content", "")
        return str(content).strip()

    client = openai_chat_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    content = response.choices[0].message.content or ""
    return content.strip()
