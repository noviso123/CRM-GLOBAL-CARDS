from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate, StageCreate
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/api/opportunities", tags=["Oportunidades e Funil"])


class StageMovePatch(BaseModel):
    ID_ETAPA: str
    MOT_PERDA: Optional[str] = None


@router.get("/funnels")
def list_funnels(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    check_permission(mgr, user, "OPORTUNIDADES", "view")
    return OpportunityService(mgr).list_funnels_with_stages()


@router.post("/funnels/stages", status_code=status.HTTP_201_CREATED)
def create_stage(
    payload: StageCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    return OpportunityService(mgr).create_stage(payload)


@router.put("/funnels/stages/{stage_id}")
def update_stage(
    stage_id: str,
    payload: Dict[str, Any],
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    return OpportunityService(mgr).update_stage(stage_id, payload)


@router.get("")
def list_opportunities(
    funnel_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    situacao: Optional[str] = None,
    client_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "OPORTUNIDADES", "view")
    rows = OpportunityService(mgr).list_opportunities(
        funnel_id=funnel_id,
        stage_id=stage_id,
        situacao=situacao,
        client_id=client_id,
        search=search,
    )
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "OPORTUNIDADES", "create")
    return OpportunityService(mgr).create_opportunity(payload, user_id=user["ID"])


@router.get("/{opp_id}")
def get_opportunity(
    opp_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "OPORTUNIDADES", "view")
    return OpportunityService(mgr).get_opportunity(opp_id)


@router.put("/{opp_id}")
def update_opportunity(
    opp_id: str,
    payload: OpportunityUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "OPORTUNIDADES", "edit")
    return OpportunityService(mgr).update_opportunity(opp_id, payload, user_id=user["ID"])


@router.patch("/{opp_id}/stage")
def move_opportunity_stage(
    opp_id: str,
    payload: StageMovePatch,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "OPORTUNIDADES", "edit")
    return OpportunityService(mgr).move_stage(
        opp_id,
        payload.ID_ETAPA,
        motivo_perda=payload.MOT_PERDA,
        user_id=user["ID"],
    )

