"""Admin ops dashboard — service health and platform statistics."""

from __future__ import annotations

import logging

import redis
from vector_store.qdrant_store import get_qdrant_client

from config import settings
from db import db_cursor
from schemas.admin import (
    OpsDashboardResponse,
    PlatformConfig,
    PlatformTotals,
    RepositoryOpsRow,
    ServiceHealth,
)
from vector_store import get_embedding_summary
from vector_store.embeddings import EMBEDDING_DIMENSION, MODEL_NAME

logger = logging.getLogger(__name__)


def _list_repositories_for_ops() -> list[dict]:
    """All repositories with owner email for the admin ops dashboard."""
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT r.id, r.full_name, r.status, r.user_id, u.email AS owner_email
            FROM repositories r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
            """
        )
        return list(cursor.fetchall())


def _check_postgres() -> ServiceHealth:
    try:
        with db_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return ServiceHealth(name="postgres", status="healthy")
    except Exception as exc:
        logger.warning("Postgres health check failed.", exc_info=True)
        return ServiceHealth(name="postgres", status="unhealthy", detail=str(exc))


def _check_redis() -> ServiceHealth:
    try:
        client = redis.from_url(settings.redis_url)
        client.ping()
        return ServiceHealth(name="redis", status="healthy")
    except Exception as exc:
        logger.warning("Redis health check failed.", exc_info=True)
        return ServiceHealth(name="redis", status="unhealthy", detail=str(exc))


def _check_qdrant() -> ServiceHealth:
    try:
        client = get_qdrant_client()
        client.get_collections()
        return ServiceHealth(name="qdrant", status="healthy")
    except Exception as exc:
        logger.warning("Qdrant health check failed.", exc_info=True)
        return ServiceHealth(name="qdrant", status="unhealthy", detail=str(exc))


def get_ops_dashboard() -> dict:
    """Build ops dashboard payload for the admin UI."""
    repositories = _list_repositories_for_ops()
    repo_rows: list[RepositoryOpsRow] = []
    chat_ready_count = 0
    hybrid_ready_count = 0
    graph_ready_count = 0
    cloned_count = 0

    for repository in repositories:
        summary = get_embedding_summary(repository["id"])
        chat_ready = summary["vector_count"] > 0
        hybrid_ready = summary["hybrid_ready"]
        graph_ready = summary["graph_ready"]

        if repository["status"] == "cloned":
            cloned_count += 1
        if chat_ready:
            chat_ready_count += 1
        if hybrid_ready:
            hybrid_ready_count += 1
        if graph_ready:
            graph_ready_count += 1

        repo_rows.append(
            RepositoryOpsRow(
                repository_id=repository["id"],
                full_name=repository["full_name"],
                status=repository["status"],
                user_id=repository.get("user_id"),
                owner_email=repository.get("owner_email"),
                chat_ready=chat_ready,
                hybrid_ready=hybrid_ready,
                graph_ready=graph_ready,
            )
        )

    totals = PlatformTotals(
        repository_count=len(repositories),
        cloned_repository_count=cloned_count,
        chat_ready_repository_count=chat_ready_count,
        hybrid_ready_repository_count=hybrid_ready_count,
        graph_ready_repository_count=graph_ready_count,
    )

    config = PlatformConfig(
        app_version=settings.app_version,
        llm_provider=settings.llm_provider,
        ollama_model=settings.ollama_model,
        openai_model=settings.openai_model,
        embedding_model=MODEL_NAME,
        embedding_dimension=EMBEDDING_DIMENSION,
        rerank_model=settings.rerank_model,
        hybrid_search_enabled=settings.hybrid_search_enabled,
        rerank_enabled=settings.rerank_enabled,
        graph_rag_enabled=settings.graph_rag_enabled,
        agents_enabled=settings.agents_enabled,
    )

    services = [
        ServiceHealth(name="api", status="healthy"),
        _check_postgres(),
        _check_redis(),
        _check_qdrant(),
    ]

    return OpsDashboardResponse(
        services=services,
        totals=totals,
        config=config,
        repositories=repo_rows,
    ).model_dump()
