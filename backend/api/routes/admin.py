from fastapi import APIRouter

from schemas.admin import OpsDashboardResponse
from services.admin_ops_service import get_ops_dashboard

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ops", response_model=OpsDashboardResponse)
def admin_ops_dashboard() -> OpsDashboardResponse:
    """Platform health and indexing statistics for the internal admin UI."""
    return OpsDashboardResponse.model_validate(get_ops_dashboard())
