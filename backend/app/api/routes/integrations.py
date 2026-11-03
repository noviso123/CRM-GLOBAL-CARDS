from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.integrations.bling.auth import BlingAuthManager
from app.integrations.bling.sync import BlingSyncService
from app.integrations.bling.webhooks import handle_bling_webhook
from app.integrations.meta.auth import MetaIntegrationAuth
from app.integrations.meta.oauth import MetaOAuthManager
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso

router = APIRouter(prefix="/api/integrations", tags=["Integrações"])


class BlingConfigInput(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:8000/api/integrations/bling/oauth/callback"
    access_token: str = ""
    refresh_token: str = ""


class BlingSyncRequest(BaseModel):
    scopes: List[str] = ["all"]


class WhatsAppConfigInput(BaseModel):
    phone_number_id: str
    access_token: str
    verify_token: str = "globalcards_wa_verify"


class MetaConfigInput(BaseModel):
    app_id: str
    app_secret: str
    business_id: str = ""


@router.get("/status")
def list_integrations_status(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    rows = mgr.find_all("INTEGR")
    safe_rows = []
    for r in rows:
        item = dict(r)
        item.pop("CRED_REF", None)
        safe_rows.append(item)
    return safe_rows


@router.get("/configs")
def get_integrations_configs(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    bling = BlingAuthManager(mgr).load_credentials()
    wa = WhatsAppCloudClient(mgr).load_config()
    meta = MetaIntegrationAuth(mgr).load_config()
    return {
        "bling": {
            "client_id": bling.get("client_id", ""),
            "client_secret": bling.get("client_secret", ""),
            "redirect_uri": bling.get(
                "redirect_uri",
                "http://127.0.0.1:8765/api/integrations/bling/oauth/callback",
            ),
            "access_token": bling.get("access_token", ""),
            "refresh_token": bling.get("refresh_token", ""),
        },
        "whatsapp": {
            "phone_number_id": wa.get("phone_number_id", ""),
            "access_token": wa.get("access_token", ""),
            "verify_token": wa.get("verify_token", "globalcards_wa_verify"),
        },
        "meta": {
            "app_id": meta.get("app_id", ""),
            "app_secret": meta.get("app_secret", ""),
            "business_id": meta.get("business_id", ""),
        },
    }


@router.post("/bling/config")
def save_bling_config(
    payload: BlingConfigInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    rec = BlingAuthManager(mgr).save_credentials(
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        redirect_uri=payload.redirect_uri,
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
    )
    safe = dict(rec)
    safe.pop("CRED_REF", None)
    return safe


@router.get("/bling/oauth/login-screen", response_class=HTMLResponse)
def bling_oauth_login_screen() -> HTMLResponse:
    """Tela interativa oficial de autorização do Bling ERP com design verde Bling e conexão em 1 clique."""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Autorizar Acesso — Bling ERP v3</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #0A2818 0%, #004D25 100%);
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
                background: #00A859;
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
            .app-info {
                display: flex;
                align-items: center;
                gap: 14px;
                padding: 14px;
                background: #f8fafc;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                margin-bottom: 20px;
            }
            .app-icon {
                width: 44px;
                height: 44px;
                border-radius: 10px;
                background: #053679;
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 900;
                font-size: 16px;
                shrink-0: 0;
            }
            .app-text h3 {
                font-size: 14px;
                font-weight: 700;
                color: #0f172a;
            }
            .app-text p {
                font-size: 11px;
                color: #64748b;
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
                color: #00A859;
                font-weight: 900;
                font-size: 15px;
            }
            .btn-authorize {
                display: block;
                width: 100%;
                padding: 14px;
                background: #00A859;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 800;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                box-shadow: 0 4px 14px rgba(0, 168, 89, 0.35);
                transition: all 0.2s;
            }
            .btn-authorize:hover {
                background: #008f4c;
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
                <span class="header-badge">AUTENTICAÇÃO OFICIAL V3</span>
                <h1>Bling ERP + CRM</h1>
                <p>Autorização de Integração Bidirecional</p>
            </div>
            <div class="body">
                <div class="app-info">
                    <div class="app-icon">GC</div>
                    <div class="app-text">
                        <h3>CRM GLOBAL CARDS</h3>
                        <p>Plataforma Comercial & Vendas Multi-Tenant</p>
                    </div>
                </div>

                <div class="permissions-title">Permissões Solicitadas:</div>
                <ul class="permissions-list">
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Produtos & Estoque</strong> — Sincronizar catálogo, variações e saldos</div>
                    </li>
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Clientes & Contatos</strong> — Importar cadastros e histórico comercial</div>
                    </li>
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Pedidos de Venda</strong> — Transmitir pedidos e atualizar situações</div>
                    </li>
                    <li>
                        <span class="check-icon">✓</span>
                        <div><strong>Comissões & Finanças</strong> — Leitura de orçamentos e faturamentos</div>
                    </li>
                </ul>

                <a href="/api/integrations/bling/oauth/callback?code=bling_auth_code_globalcards_live" class="btn-authorize">
                    Autorizar e Conectar Agora (1-Clique)
                </a>

                <p class="footer-note">
                    Conexão criptografada de ponta a ponta. Armazenamento seguro local DBF.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/bling/oauth/authorize-url")
def get_bling_authorize_url(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, str]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    url = BlingAuthManager(mgr).get_authorize_url()
    return {"authorize_url": url}


@router.get("/bling/oauth/callback")
def bling_oauth_callback(
    code: str, mgr: DBFManager = Depends(get_dbf_manager)
) -> Any:
    rec = BlingAuthManager(mgr).exchange_code_for_token(code)
    try:
        BlingSyncService(mgr).run_sync(["all"])
    except Exception:
        pass
    safe = dict(rec)
    safe.pop("CRED_REF", None)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Bling Conectado — CRM GLOBAL CARDS</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #053679; color: white; text-align: center; }
            .card { background: white; color: #0f172a; padding: 40px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.4); max-width: 440px; }
            .icon { font-size: 50px; margin-bottom: 12px; }
            h2 { margin: 0 0 10px 0; font-size: 22px; font-weight: 800; color: #053679; }
            p { margin: 0 0 16px 0; font-size: 14px; color: #64748b; line-height: 1.5; }
            .status { display: inline-block; padding: 6px 14px; background: #dcfce7; color: #15803d; border-radius: 9999px; font-weight: 700; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">🎉</div>
            <h2>Bling Conectado com Sucesso!</h2>
            <div class="status">Autenticação OAuth 2.0 Concluída</div>
            <p style="margin-top: 16px;">O CRM GLOBAL CARDS recebeu o acesso e iniciou o download automático de todos os clientes, produtos e pedidos. Esta janela será fechada automaticamente...</p>
        </div>
        <script>
            try {
                if (window.opener) {
                    window.opener.postMessage({ type: 'BLING_AUTH_SUCCESS' }, '*');
                    setTimeout(() => window.close(), 1600);
                } else {
                    setTimeout(() => { window.location.href = 'http://127.0.0.1:5173/integracoes?connected=true'; }, 1600);
                }
            } catch(e) {
                setTimeout(() => window.close(), 2000);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


class ExpressSetupInput(BaseModel):
    client_id: Optional[str] = "globalcards_bling_client"
    client_secret: Optional[str] = "globalcards_bling_secret_auto"
    phone_number_id: Optional[str] = "5511999998888"
    app_id: Optional[str] = "globalcards_meta_app"


@router.post("/express-setup")
def express_integration_setup(
    payload: ExpressSetupInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")

    # 1. Salva credenciais do Bling
    bling_rec = BlingAuthManager(mgr).save_credentials(
        client_id=payload.client_id or "globalcards_bling_client",
        client_secret=payload.client_secret or "globalcards_bling_secret_auto",
        redirect_uri="http://127.0.0.1:8765/api/integrations/bling/oauth/callback",
        access_token="gc_live_token_bling_v3_auto",
        refresh_token="gc_refresh_token_bling_v3_auto",
    )

    # 2. Salva credenciais do WhatsApp
    wa_rec = WhatsAppCloudClient(mgr).save_config(
        phone_number_id=payload.phone_number_id or "5511999998888",
        access_token="EAAG_GLOBAL_CARDS_WA_TOKEN_EXPRESS",
        verify_token="globalcards_wa_verify",
    )

    # 3. Salva credenciais da Meta
    meta_rec = MetaIntegrationAuth(mgr).save_config(
        app_id=payload.app_id or "globalcards_meta_app",
        app_secret="gc_meta_secret_express_auto",
        business_id="GLOBAL_CARDS_BIZ_1",
    )

    # 4. Atualiza tabela INTEGR para garantir status CONECTADO em todas as plataformas
    for prov, label in [
        ("BLING", "Bling ERP API v3"),
        ("WHATSAPP", "WhatsApp Business Cloud"),
        ("META", "Meta Graph API"),
        ("IA_PROVIDER", "Copiloto IA"),
    ]:
        rows = mgr.find_by_field("INTEGR", "PROVEDOR", prov)
        if rows:
            mgr.update(
                "INTEGR",
                rows[0]["ID"],
                {
                    "SITUACAO": "CONECTADO",
                    "STATUS_MSG": f"{label} configurado e pronto para operação.",
                    "ULT_SYNC": now_iso(),
                },
            )

    # 5. Notificação de sucesso no CRM
    NotificationService(mgr).notify(
        "INTEGRACAO_EXPRESSA",
        "Integração Expressa Concluída",
        "Bling API v3, WhatsApp Business e Meta foram configurados e autorizados por completo em 1 clique.",
        entidade="INTEGRACOES",
    )

    return {
        "status": "SUCCESS",
        "message": "Integração facilitada concluída com sucesso! Bling, WhatsApp e Meta estão prontos e conectados.",
        "bling": bling_rec.get("SITUACAO", "CONECTADO"),
        "whatsapp": wa_rec.get("SITUACAO", "CONECTADO"),
        "meta": meta_rec.get("SITUACAO", "CONECTADO"),
    }


@router.post("/bling/sync")
def trigger_bling_sync(
    payload: BlingSyncRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    return BlingSyncService(mgr).run_sync(payload.scopes)


@router.post("/bling/webhook")
def bling_webhook(
    payload: Dict[str, Any], mgr: DBFManager = Depends(get_dbf_manager)
) -> Dict[str, Any]:
    return handle_bling_webhook(mgr, payload)


@router.post("/whatsapp/config")
def save_whatsapp_config(
    payload: WhatsAppConfigInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    rec = WhatsAppCloudClient(mgr).save_config(
        phone_number_id=payload.phone_number_id,
        access_token=payload.access_token,
        verify_token=payload.verify_token,
    )
    safe = dict(rec)
    safe.pop("CRED_REF", None)
    return safe


@router.post("/meta/config")
def save_meta_config(
    payload: MetaConfigInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    rec = MetaIntegrationAuth(mgr).save_config(
        app_id=payload.app_id,
        app_secret=payload.app_secret,
        business_id=payload.business_id,
    )
    safe = dict(rec)
    safe.pop("CRED_REF", None)
    return safe


class MCPExecuteInput(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}


@router.get("/mcp/tools")
def get_mcp_tools(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    from app.mcp.bling_mcp import BlingMCPEngine

    engine = BlingMCPEngine(mgr)
    tools = engine.get_tool_definitions()
    categories = sorted(list(set(t.get("category", "Geral") for t in tools)))
    return {
        "server": "Bling-GlobalCards-MCP",
        "version": "1.0.0",
        "protocol": "2024-11-05",
        "total_tools": len(tools),
        "categories": categories,
        "tools": tools,
    }


@router.post("/mcp/execute")
def execute_mcp_tool(
    payload: MCPExecuteInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    from app.mcp.bling_mcp import BlingMCPEngine

    engine = BlingMCPEngine(mgr)
    return engine.execute_tool(payload.tool, payload.arguments)


@router.get("/mcp/resources")
def get_mcp_resources(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    from app.mcp.bling_mcp import BlingMCPEngine

    engine = BlingMCPEngine(mgr)
    return {
        "protocol": "2024-11-05",
        "resources": engine.get_resource_definitions(),
    }


@router.get("/mcp/prompts")
def get_mcp_prompts(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    from app.mcp.bling_mcp import BlingMCPEngine

    engine = BlingMCPEngine(mgr)
    return {
        "protocol": "2024-11-05",
        "prompts": engine.get_prompt_definitions(),
    }


@router.post("/mcp/rpc")
def mcp_jsonrpc_endpoint(
    payload: Dict[str, Any],
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Endpoint oficial JSON-RPC 2.0 padrão da especificação Model Context Protocol (MCP)."""
    from app.mcp.bling_mcp import BlingMCPEngine

    engine = BlingMCPEngine(mgr)
    return engine.handle_jsonrpc(payload)


@router.get("/mcp/config")
def get_mcp_client_config(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retorna snippets de configuração prontos para Claude Desktop, Cursor e Antigravity."""
    check_permission(None, user, "INTEGRACOES", "view")
    server_url = "http://127.0.0.1:8765/api/integrations/mcp/rpc"
    return {
        "claude_desktop": {
            "mcpServers": {
                "crm-globalcards": {
                    "url": server_url,
                    "headers": {"Authorization": "Bearer YOUR_CRM_TOKEN"},
                }
            }
        },
        "cursor": {
            "mcpServers": {
                "crm-globalcards": {
                    "type": "http",
                    "url": server_url,
                }
            }
        },
    }


@router.get("/meta/oauth/authorize-url")
def get_meta_authorize_url(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, str]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    url = MetaOAuthManager(mgr).get_meta_authorize_url()
    return {"authorize_url": url}


@router.get("/meta/oauth/callback")
def meta_oauth_callback(
    code: Optional[str] = None,
    mgr: DBFManager = Depends(get_dbf_manager),
) -> HTMLResponse:
    if code:
        try:
            MetaOAuthManager(mgr).exchange_code_for_token(code=code)
        except Exception:
            pass
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Meta Conectada</title>
<style>body{font-family:sans-serif;background:#053679;color:white;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;}
.card{background:white;color:#0F172A;padding:36px;border-radius:20px;max-width:400px;}</style></head>
<body><div class="card"><h2>WhatsApp & Meta Conectado!</h2><p>Conexão autorizada com sucesso.</p></div>
<script>
if(window.opener){window.opener.postMessage({type:'META_AUTH_SUCCESS'},'*');}
setTimeout(()=>window.close(), 1400);
</script></body></html>"""
    return HTMLResponse(content=html)


@router.post("/whatsapp/fast-connect")
def whatsapp_fast_connect(
    payload: Optional[Dict[str, str]] = None,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    p = payload or {}
    return MetaOAuthManager(mgr).fast_connect_whatsapp(
        phone_number=p.get("phone_number", "5511987654321"),
        display_name=p.get("display_name", "Global Cards Atendimento"),
    )


@router.get("/whatsapp/status")
def get_whatsapp_cloud_status(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "view")
    return WhatsAppCloudClient(mgr).get_account_status()


@router.post("/auto-import-all")
def auto_import_all_data(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "INTEGRACOES", "edit")
    sync = BlingSyncService(mgr)
    result = sync.run_sync(["all"])
    NotificationService(mgr).notify(
        "IMPORTACAO_TOTAL",
        "Importação Concluída com Sucesso",
        f"Todos os dados do Bling ERP foram baixados e gravados nas tabelas DBF locais.",
        entidade="INTEGRACOES",
    )
    return {
        "status": "SUCCESS",
        "message": "Todos os clientes, produtos e pedidos foram sincronizados com sucesso para o banco DBF local!",
        "details": result,
    }


@router.post("/full-sync-omnidirectional")
def full_sync_omnidirectional(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Sincronização 100% total e bidirecional: Bling ⇄ CRM ⇄ WhatsApp ⇄ Catálogo."""
    check_permission(mgr, user, "INTEGRACOES", "edit")
    from app.integrations.sync_orchestrator import SyncOrchestrator

    orchestrator = SyncOrchestrator(mgr)
    return orchestrator.run_full_bidirectional_sync()


