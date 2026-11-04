from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user, get_dbf_manager
from app.database.dbf_manager import DBFManager
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notificações"])


@router.get("")
def list_notifications(
    unread_only: bool = False,
    tipo: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    return NotificationService(mgr).list_notifications(
        user_id=user["ID"], unread_only=unread_only, tipo=tipo
    )


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    rec = NotificationService(mgr).mark_read(notification_id)
    return rec or {"id": notification_id, "LIDA": True}


@router.post("/read-all")
def mark_all_notifications_read(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    count = NotificationService(mgr).mark_all_read(user["ID"])
    return {"marked_read": count}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    ok = NotificationService(mgr).delete_notification(notification_id)
    return {"id": notification_id, "deleted": ok}


@router.delete("")
def clear_all_notifications_delete(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    count = NotificationService(mgr).clear_all(user["ID"])
    return {"cleared": count}


@router.post("/clear-all")
def clear_all_notifications_post(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    count = NotificationService(mgr).clear_all(user["ID"])
    return {"cleared": count}

