from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/api/activities", tags=["Atividades"])


class RescheduleRequest(BaseModel):
    DATA_AG: str
    HORA_AG: str = "09:00"


@router.get("")
def list_activities(
    situacao: Optional[str] = None,
    tipo: Optional[str] = None,
    client_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "view")
    rows = ActivityService(mgr).list_activities(
        situacao=situacao, tipo=tipo, client_id=client_id
    )
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "create")
    return ActivityService(mgr).create_activity(payload, user_id=user["ID"])


@router.put("/{activity_id}")
def update_activity(
    activity_id: str,
    payload: ActivityUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "edit")
    return ActivityService(mgr).update_activity(activity_id, payload, user_id=user["ID"])


@router.patch("/{activity_id}/complete")
def complete_activity(
    activity_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "edit")
    return ActivityService(mgr).complete_activity(activity_id, user_id=user["ID"])


@router.patch("/{activity_id}/reschedule")
def reschedule_activity(
    activity_id: str,
    payload: RescheduleRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "edit")
    return ActivityService(mgr).reschedule_activity(
        activity_id, payload.DATA_AG, payload.HORA_AG, user_id=user["ID"]
    )


@router.patch("/{activity_id}/cancel")
def cancel_activity(
    activity_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ATIVIDADES", "edit")
    return ActivityService(mgr).cancel_activity(activity_id, user_id=user["ID"])

