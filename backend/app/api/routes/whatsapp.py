from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.exceptions import ValidationErrorCRM
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.integrations.meta.oauth import MetaOAuthManager
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.integrations.whatsapp.messages import WhatsAppService
from app.integrations.whatsapp.webhooks import handle_whatsapp_webhook

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp & Meta"])


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


class FastConnectInput(BaseModel):
    phone_number: str = "5511987654321"
    display_name: str = "Global Cards Atendimento Oficial"


class TestSendInput(BaseModel):
    to_phone: str
    message: str = "Global Cards - Teste de conexão oficial WhatsApp Business Cloud realizado com sucesso!"


class SendTemplateInput(BaseModel):
    template_name: str
    parameters: List[str] = []


# =========================================================================
# GESTÃO DA CONEXÃO WHATSAPP / META
# =========================================================================

@router.get("/status")
def get_whatsapp_status(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Retorna detalhes da linha, status da conexão Meta Cloud e dados do webhook."""
    check_permission(mgr, user, "WHATSAPP", "view")
    return WhatsAppCloudClient(mgr).get_account_status()


@router.get("/oauth/authorize-url")
def get_meta_authorize_url(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, str]:
    """Gera URL de autorização oficial da Meta / Facebook Login for Business."""
    check_permission(mgr, user, "INTEGRACOES", "edit")
    url = MetaOAuthManager(mgr).get_meta_authorize_url()
    return {"authorize_url": url}


@router.get("/oauth/callback")
def meta_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    mgr: DBFManager = Depends(get_dbf_manager),
) -> HTMLResponse:
    """Callback oficial da Meta após autorização do WhatsApp Embedded Signup."""
    details = {}
    if code:
        try:
            details = MetaOAuthManager(mgr).exchange_code_for_token(code=code)
        except Exception as exc:
            details = {"status": "ERROR", "message": str(exc)}

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>WhatsApp & Meta Conectado - CRM GLOBAL CARDS</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #053679;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            text-align: center;
        }}
        .card {{
            background: white;
            color: #0F172A;
            padding: 36px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            max-width: 440px;
        }}
        .icon {{
            font-size: 52px;
            margin-bottom: 16px;
        }}
        h2 {{ margin: 0 0 10px; color: #053679; font-weight: 800; }}
        p {{ color: #475569; font-size: 14px; margin: 0 0 16px; }}
        .badge {{
            display: inline-block;
            background: #ECFDF5;
            color: #065F46;
            border: 1px solid #A7F3D0;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">💬</div>
        <h2>WhatsApp Conectado!</h2>
        <p>A linha comercial da Meta foi autorizada com sucesso pelo CRM GLOBAL CARDS.</p>
        <div class="badge">CONEXÃO META ATIVA</div>
        <p style="margin-top: 18px; font-size: 12px; color: #94A3B8;">Esta janela fechará automaticamente...</p>
    </div>
    <script>
        if (window.opener) {{
            window.opener.postMessage({{
                type: 'META_AUTH_SUCCESS',
                payload: {details}
            }}, '*');
        }}
        setTimeout(function() {{
            window.close();
        }}, 1400);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


@router.post("/fast-connect")
def fast_connect_whatsapp(
    payload: FastConnectInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Conexão Instantânea em 1-Clique sem formulários manuais nem burocracia."""
    check_permission(mgr, user, "INTEGRACOES", "edit")
    return MetaOAuthManager(mgr).fast_connect_whatsapp(
        phone_number=payload.phone_number, display_name=payload.display_name
    )


@router.post("/test-send")
def test_send_whatsapp(
    payload: TestSendInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Dispara mensagem de validação em tempo real via Meta Cloud API."""
    check_permission(mgr, user, "WHATSAPP", "create")
    if not payload.to_phone:
        raise ValidationErrorCRM("Informe o telefone para o teste.")
    res = WhatsAppCloudClient(mgr).send_cloud_text_message(
        to_phone=payload.to_phone, text_body=payload.message
    )
    return {
        "status": "SENT" if res.get("dispatched_external") else "FAILED",
        "result": res,
    }


@router.get("/templates")
def list_whatsapp_templates(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    """Lista templates HSM pré-aprovados pela Meta para disparo rápido de avisos."""
    check_permission(mgr, user, "WHATSAPP", "view")
    return WhatsAppService(mgr).list_templates()


# =========================================================================
# WEBHOOK OFICIAL DA META GRAPH API (GET & POST)
# =========================================================================

@router.get("/webhook", response_class=PlainTextResponse)
def verify_meta_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Any:
    """Verificação de webhook exigida pela Meta (WhatsApp Business Cloud API)."""
    cfg = WhatsAppCloudClient(mgr).load_config()
    expected_token = cfg.get("verify_token", "globalcards_wa_verify")

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return str(hub_challenge or "")
    return PlainTextResponse(content="Token de verificação inválido", status_code=403)


@router.post("/webhook")
def whatsapp_webhook(
    payload: Dict[str, Any], mgr: DBFManager = Depends(get_dbf_manager)
) -> Dict[str, Any]:
    """Recebe mensagens e status de entrega enviados pela Meta Graph API."""
    return handle_whatsapp_webhook(mgr, payload)


# =========================================================================
# CONVERSAS E MENSAGENS COMERCIAIS
# =========================================================================

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


@router.post("/conversations/{conv_id}/send-template", status_code=status.HTTP_201_CREATED)
def send_template_to_conversation(
    conv_id: str,
    payload: SendTemplateInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Envia template oficial da Meta para o contato da conversa selecionada."""
    check_permission(mgr, user, "WHATSAPP", "create")
    return WhatsAppService(mgr).send_template(
        conv_id=conv_id,
        template_name=payload.template_name,
        parameters=payload.parameters,
        user_id=user["ID"],
    )
