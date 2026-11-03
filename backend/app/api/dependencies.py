from typing import Any, Dict, List
from fastapi import Depends, Header, Request
from app.core.exceptions import AuthenticationErrorCRM
from app.core.security import decode_access_token
from app.database.dbf_manager import DBFManager, dbf_manager


def get_dbf_manager(request: Request) -> DBFManager:
    mgr = getattr(request.app.state, "dbf_manager", None)
    return mgr if mgr is not None else dbf_manager


def get_current_user(
    request: Request,
    authorization: str = Header(default=""),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationErrorCRM("Cabeçalho de autorização Bearer ausente.")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_access_token(token)
    user_id = claims.get("sub", "")
    user = mgr.get_by_id("USUARIOS", user_id)
    if not user or user.get("SITUACAO") != "ATIVO":
        raise AuthenticationErrorCRM("Sessão inválida ou usuário inativo.")
    return user


def paginate_items(items: List[Dict[str, Any]], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    p = max(1, page)
    ps = max(1, min(200, page_size))
    total = len(items)
    total_pages = max(1, (total + ps - 1) // ps)
    start = (p - 1) * ps
    end = start + ps
    return {
        "items": items[start:end],
        "total": total,
        "page": p,
        "page_size": ps,
        "total_pages": total_pages,
    }

