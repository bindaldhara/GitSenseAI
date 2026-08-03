from fastapi import APIRouter

from cache.analytics import get_cache_analytics, reset_cache_analytics
from cache.semantic_cache import clear_all_semantic_cache
from schemas.admin import CacheAnalyticsResponse, CacheClearResponse, OpsDashboardResponse
from services.admin_ops_service import get_ops_dashboard

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ops", response_model=OpsDashboardResponse)
def admin_ops_dashboard() -> OpsDashboardResponse:
    """Platform health and indexing statistics for the internal admin UI."""
    return OpsDashboardResponse.model_validate(get_ops_dashboard())


@router.get("/cache", response_model=CacheAnalyticsResponse)
def admin_cache_analytics() -> CacheAnalyticsResponse:
    """Semantic cache hit/miss analytics for the internal admin UI."""
    return CacheAnalyticsResponse.model_validate(get_cache_analytics())


@router.delete("/cache", response_model=CacheClearResponse)
def admin_clear_cache() -> CacheClearResponse:
    """Clear all semantic cache entries and reset analytics counters."""
    removed = clear_all_semantic_cache()
    reset_cache_analytics()
    return CacheClearResponse(
        removed_keys=removed,
        message="Semantic cache cleared and analytics reset.",
    )
