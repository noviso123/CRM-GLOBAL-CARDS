from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_current_user, get_dbf_manager
from app.database.dbf_manager import DBFManager
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["Pesquisa Global"])


@router.get("")
def global_search(
    q: str = Query(default=""),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, List[Dict[str, Any]]]:
    return SearchService(mgr).global_search(q)

