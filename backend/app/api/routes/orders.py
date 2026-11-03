from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.order import OrderCreate
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["Pedidos"])


class OrderStatusPatch(BaseModel):
    SITUACAO: str


@router.get("")
def list_orders(
    search: Optional[str] = None,
    situacao: Optional[str] = None,
    client_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PEDIDOS", "view")
    rows = OrderService(mgr).list_orders(search=search, situacao=situacao, client_id=client_id)
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PEDIDOS", "create")
    return OrderService(mgr).create_order(payload, user_id=user["ID"])


@router.get("/{order_id}")
def get_order(
    order_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PEDIDOS", "view")
    return OrderService(mgr).get_order(order_id)


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: OrderStatusPatch,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PEDIDOS", "edit")
    return OrderService(mgr).update_status(order_id, payload.SITUACAO, user_id=user["ID"])

