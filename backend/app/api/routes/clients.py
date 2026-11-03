import csv
import io
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.client import AddressCreate, ClientCreate, ClientUpdate
from app.services.client_service import ClientService

router = APIRouter(prefix="/api/clients", tags=["Clientes"])


class StatusPatch(BaseModel):
    SITUACAO: str


@router.get("")
def list_clients(
    search: Optional[str] = None,
    situacao: Optional[str] = None,
    uf: Optional[str] = None,
    origem: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "view")
    svc = ClientService(mgr)
    rows = svc.list_clients(search=search, situacao=situacao, uf=uf, origem=origem)
    return paginate_items(rows, page=page, page_size=page_size)


@router.get("/export/csv")
def export_clients_csv(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> StreamingResponse:
    check_permission(mgr, user, "CLIENTES", "export")
    svc = ClientService(mgr)
    rows = svc.list_clients()
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    headers = ["CODIGO", "TIPO_PES", "NOME", "FANTASIA", "CPF_CNPJ", "EMAIL", "TELEFONE", "CELULAR", "CIDADE", "UF", "SITUACAO", "ORIGEM", "DT_CRIA"]
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r.get(h, "") for h in headers])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=clientes_globalcards.csv"},
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "create")
    svc = ClientService(mgr)
    return svc.create_client(payload, user_id=user["ID"])


@router.get("/{client_id}")
def get_client(
    client_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "view")
    return ClientService(mgr).get_client(client_id)


@router.get("/{client_id}/overview")
def get_client_overview(
    client_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "view")
    return ClientService(mgr).get_client_overview_10_tabs(client_id)


@router.put("/{client_id}")
def update_client(
    client_id: str,
    payload: ClientUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "edit")
    return ClientService(mgr).update_client(client_id, payload, user_id=user["ID"])


@router.patch("/{client_id}/status")
def patch_client_status(
    client_id: str,
    payload: StatusPatch,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "edit")
    return ClientService(mgr).update_client(
        client_id, ClientUpdate(SITUACAO=payload.SITUACAO.upper()), user_id=user["ID"]
    )


@router.post("/{client_id}/addresses", status_code=status.HTTP_201_CREATED)
def add_client_address(
    client_id: str,
    payload: AddressCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "edit")
    return ClientService(mgr).add_address(client_id, payload, user_id=user["ID"])


@router.delete("/{client_id}")
def delete_client(
    client_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CLIENTES", "delete")
    ClientService(mgr).delete_client(client_id, user_id=user["ID"])
    return {"deleted": True, "id": client_id}

