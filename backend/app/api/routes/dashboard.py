from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    period_days: int = Query(default=30, ge=1, le=3650),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "DASHBOARD", "view")
    svc = DashboardService(mgr)
    return svc.get_summary(period_days=period_days)

