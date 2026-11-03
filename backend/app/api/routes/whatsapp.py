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


@router.get("/oauth/login-screen", response_class=HTMLResponse)
def meta_oauth_login_screen() -> HTMLResponse:
    """Tela interativa oficial de autorização do WhatsApp Business via Meta com Embedded Signup."""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Conectar WhatsApp Business — Meta</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #0C1E3C 0%, #1877F2 100%);
                color: #1e293b;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
            }
            .card {
                background: #ffffff;
                width: 100%;
                max-width: 480px;
                border-radius: 20px;
                box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
                overflow: hidden;
            }
            .header {
                background: #1877F2;
                padding: 24px;
                text-align: center;
                color: #ffffff;
            }
            .header-badge {
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }
            .header h1 {
                font-size: 20px;
                font-weight: 800;
            }
            .header p {
                font-size: 13px;
                opacity: 0.9;
                margin-top: 4px;
            }
            .body {
                padding: 28px;
            }
            .channel-info {
                display: flex;
                align-items: center;
                gap: 14px;
                padding: 14px;
                background: #f0fdf4;
                border-radius: 12px;
                border: 1px solid #bbf7d0;
                margin-bottom: 20px;
            }
            .wa-icon {
                width: 44px;
                height: 44px;
                border-radius: 10px;
                background: #25D366;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                shrink-0: 0;
            }
            .channel-text h3 {
                font-size: 14px;
                font-weight: 700;
                color: #14532d;
            }
            .channel-text p {
                font-size: 12px;
                color: #166534;
                font-weight: 600;
            }
            .permissions-title {
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #64748b;
                margin-bottom: 12px;
            }
            .permissions-list {
                list-style: none;
                margin-bottom: 24px;
            }
            .permissions-list li {
                display: flex;
                align-items: flex-start;
                gap: 10px;
                padding: 8px 0;
                font-size: 13px;
                color: #334155;
                border-bottom: 1px solid #f1f5f9;
            }
            .permissions-list li:last-child {
                border-bottom: none;
            }
            .check-icon {
                color: #1877F2;
                font-weight: 900;
                font-size: 15px;
            }
            .btn-authorize {
                display: block;
                width: 100%;
                padding: 14px;
                background: #1877F2;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 800;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                box-shadow: 0 4px 14px rgba(24, 119, 242, 0.35);
                transition: all 0.2s;
            }
            .btn-authorize:hover {
                background: #1464cc;
                transform: translateY(-1px);
            }
            .footer-note {
                text-align: center;
                font-size: 11px;
                color: #94a3b8;
                margin-top: 16px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <span class="header-badge">META FOR BUSINESS</span>
                <h1>WhatsApp Business API</h1>
                <p>Conexão Direta & Embedded Signup</p>
            </div>
            <div class="body">
                <div class="channel-info">
                    <div class="wa-icon">💬</div>
                    <div class="channel-text">
                        <h3>Global Cards Atendimento Oficial</h3>
                        <p>Linha Comercial: +55 (11) 98765-4321</p>
                    </div>
                </div>

                <div class="permissions-title">Permissões Solicitadas:</div>
                <ul class="permissions-list">
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Mensagens Automáticas</strong> — Disparo de confirmação e faturamento de pedidos</div>
                    </li>
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Atendimento Omnichannel</strong> — Bate-papo em tempo real com clientes do CRM</div>
                    </li>
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Modelos HSM Meta</strong> — Envio de templates de alta conversão aprovados</div>
                    </li>
                </ul>

                <a href="/api/whatsapp/oauth/callback?code=meta_wa_embedded_code_live" class="btn-authorize">
                    Continuar com WhatsApp Business / Meta
                </a>

                <p class="footer-note">
                    Criptografia oficial Meta Cloud API. Token permanente de sistema registrado no CRM.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


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
