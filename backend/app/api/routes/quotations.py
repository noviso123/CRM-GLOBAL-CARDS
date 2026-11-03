from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.quotation import QuotationCreate
from app.services.quotation_service import QuotationService

router = APIRouter(prefix="/api/quotations", tags=["Orçamentos"])


class QuotationStatusPatch(BaseModel):
    SITUACAO: str


@router.get("")
def list_quotations(
    search: Optional[str] = None,
    situacao: Optional[str] = None,
    client_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ORCAMENTOS", "view")
    rows = QuotationService(mgr).list_quotations(
        search=search, situacao=situacao, client_id=client_id
    )
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ORCAMENTOS", "create")
    max_disc = float(user.get("DESC_MAX", 10.0))
    return QuotationService(mgr).create_quotation(
        payload, user_id=user["ID"], user_max_disc=max_disc
    )


@router.get("/{quotation_id}")
def get_quotation(
    quotation_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ORCAMENTOS", "view")
    return QuotationService(mgr).get_quotation(quotation_id)


@router.patch("/{quotation_id}/status")
def update_quotation_status(
    quotation_id: str,
    payload: QuotationStatusPatch,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "ORCAMENTOS", "edit")
    return QuotationService(mgr).update_status(
        quotation_id, payload.SITUACAO, user_id=user["ID"]
    )


@router.post("/{quotation_id}/convert-to-order", status_code=status.HTTP_201_CREATED)
def convert_quotation_to_order(
    quotation_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PEDIDOS", "create")
    return QuotationService(mgr).convert_to_order(quotation_id, user_id=user["ID"])

