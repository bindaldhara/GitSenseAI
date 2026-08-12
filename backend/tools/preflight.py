"""Preflight checks before MCP tools run (host-side MCP → localhost services)."""

from __future__ import annotations

import logging

import redis
from qdrant_client import QdrantClient

from config import settings
from db import db_cursor
from tools.errors import ToolError

logger = logging.getLogger(__name__)


def require_mcp_infrastructure() -> None:
    """
    Verify Postgres, Redis, and Qdrant are reachable from the MCP process.

    MCP/Codex runs on your Mac and uses POSTGRES_HOST=localhost (published Docker ports).
    Start the stack yourself before calling tools: make docker-up
    """
    errors: list[str] = []

    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        logger.warning("Postgres preflight failed: %s", exc)
        errors.append(
            f"PostgreSQL not reachable at {settings.postgres_host}:{settings.postgres_port}. "
            "Run `make docker-up` in the gitsense-ai repo (Codex cannot start Docker for you)."
        )

    try:
        client = redis.from_url(settings.redis_url)
        client.ping()
    except Exception as exc:
        logger.warning("Redis preflight failed: %s", exc)
        errors.append(
            f"Redis not reachable at {settings.redis_url}. "
            "Run `make docker-up` to start postgres, redis, and qdrant."
        )

    try:
        QdrantClient(url=settings.qdrant_url).get_collections()
    except Exception as exc:
        logger.warning("Qdrant preflight failed: %s", exc)
        errors.append(
            f"Qdrant not reachable at {settings.qdrant_url}. "
            "Run `make docker-up` and wait until containers are healthy."
        )

    if errors:
        raise ToolError(" Infrastructure not ready:\n- " + "\n- ".join(errors))
