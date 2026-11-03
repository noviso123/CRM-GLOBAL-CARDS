from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.contact_service import ContactService

router = APIRouter(prefix="/api/contacts", tags=["Contatos"])


@router.get("")
def list_contacts(
    client_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONTATOS", "view")
    rows = ContactService(mgr).list_contacts(client_id=client_id, search=search)
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONTATOS", "create")
    return ContactService(mgr).create_contact(payload, user_id=user["ID"])


@router.put("/{contact_id}")
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONTATOS", "edit")
    return ContactService(mgr).update_contact(contact_id, payload, user_id=user["ID"])


@router.delete("/{contact_id}")
def delete_contact(
    contact_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONTATOS", "delete")
    ContactService(mgr).delete_contact(contact_id)
    return {"deleted": True, "id": contact_id}

