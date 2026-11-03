from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.integrations.whatsapp.messages import WhatsAppService
from app.integrations.whatsapp.webhooks import handle_whatsapp_webhook

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


class ConversationCreate(BaseModel):
    TELEFONE: str
    NOME_CONT: str
    ID_CLIENTE: Optional[str] = ""
    ID_CONTATO: Optional[str] = ""
    ID_OPORT: Optional[str] = ""


class ConversationLinkPatch(BaseModel):
    ID_CLIENTE: Optional[str] = None
    ID_CONTATO: Optional[str] = None
    ID_OPORT: Optional[str] = None
    SITUACAO: Optional[str] = None
    OBS_ATEND: Optional[str] = None


class MessageCreate(BaseModel):
    CONTEUDO: str
    DIRECAO: str = "SAIDA"
    TIPO_MSG: str = "TEXTO"


@router.get("/conversations")
def list_conversations(
    situacao: Optional[str] = None,
    search: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    check_permission(mgr, user, "WHATSAPP", "view")
    return WhatsAppService(mgr).list_conversations(situacao=situacao, search=search)


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "WHATSAPP", "create")
    return WhatsAppService(mgr).create_or_get_conversation(
        telefone=payload.TELEFONE,
        nome_cont=payload.NOME_CONT,
        id_cliente=payload.ID_CLIENTE or "",
        id_contato=payload.ID_CONTATO or "",
        id_oport=payload.ID_OPORT or "",
        user_id=user["ID"],
    )


@router.patch("/conversations/{conv_id}/link")
def link_conversation(
    conv_id: str,
    payload: ConversationLinkPatch,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "WHATSAPP", "edit")
    return WhatsAppService(mgr).link_conversation(
        conv_id,
        id_cliente=payload.ID_CLIENTE,
        id_contato=payload.ID_CONTATO,
        id_oport=payload.ID_OPORT,
        situacao=payload.SITUACAO,
        obs_atend=payload.OBS_ATEND,
        user_id=user["ID"],
    )


@router.get("/conversations/{conv_id}/messages")
def list_messages(
    conv_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    check_permission(mgr, user, "WHATSAPP", "view")
    return WhatsAppService(mgr).list_messages(conv_id)


@router.post("/conversations/{conv_id}/messages", status_code=status.HTTP_201_CREATED)
def send_message(
    conv_id: str,
    payload: MessageCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "WHATSAPP", "create")
    return WhatsAppService(mgr).add_message(
        conv_id=conv_id,
        conteudo=payload.CONTEUDO,
        direcao=payload.DIRECAO,
        tipo_msg=payload.TIPO_MSG,
        user_id=user["ID"],
    )


@router.post("/webhook")
def whatsapp_webhook(
    payload: Dict[str, Any], mgr: DBFManager = Depends(get_dbf_manager)
) -> Dict[str, Any]:
    return handle_whatsapp_webhook(mgr, payload)

