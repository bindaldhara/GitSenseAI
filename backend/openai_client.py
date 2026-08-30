"""OpenAI-compatible chat client (OpenAI, OpenRouter, or any base_url)."""

from fastapi import HTTPException, status
from openai import OpenAI

from config import settings


def openai_chat_client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured.",
        )
    if settings.openai_base_url:
        return OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            default_headers={
                "HTTP-Referer": settings.frontend_origin,
                "X-Title": settings.app_name,
            },
        )
    return OpenAI(api_key=settings.openai_api_key)
