from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from app.api.routes import (
    activities,
    ai,
    auth,
    clients,
    contacts,
    dashboard,
    integrations,
    notifications,
    opportunities,
    orders,
    products,
    quotations,
    reports,
    search,
    settings as settings_route,
    suppliers,
    whatsapp,
)
from app.core.config import settings
from app.core.exceptions import CRMSatiroException
from app.core.logging import setup_logging, write_audit_log
from app.core.security import hash_password
from app.database.dbf_manager import DBFManager, dbf_manager
from app.database.migrations import run_startup_migrations


def create_app(custom_data_dir: Optional[Path] = None) -> FastAPI:
    setup_logging()
    mgr = DBFManager(base_data_dir=custom_data_dir) if custom_data_dir else dbf_manager
    run_startup_migrations(mgr, hash_password)
    write_audit_log("SYSTEM_STARTUP", "SISTEMA", "CRM_GLOBAL_CARDS")

    app = FastAPI(
        title="CRM GLOBAL CARDS + Bling API",
        version=settings.app_version,
        description="Backend Comercial Independente 100% Python + Motor Nativo DBF (Zero SQL) integrado ao Bling v3.",
    )
    app.state.dbf_manager = mgr

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(CRMSatiroException)
    async def crm_exception_handler(_request: Request, exc: CRMSatiroException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.get("/")
    def root(request: Request):
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>API CRM GLOBAL CARDS — Backend Online</title>
                <style>
                    body {{
                        margin: 0;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        background: linear-gradient(135deg, #031E44 0%, #053679 50%, #042A5F 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #ffffff;
                        padding: 20px;
                        box-sizing: border-box;
                    }}
                    .card {{
                        background: #ffffff;
                        color: #1e293b;
                        border-radius: 20px;
                        padding: 40px;
                        max-width: 520px;
                        width: 100%;
                        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
                        text-align: center;
                    }}
                    .badge {{
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        padding: 6px 14px;
                        background: #dcfce7;
                        color: #166534;
                        font-size: 12px;
                        font-weight: 800;
                        border-radius: 9999px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 16px;
                    }}
                    .badge-dot {{
                        width: 8px;
                        height: 8px;
                        background: #22c55e;
                        border-radius: 50%;
                        display: inline-block;
                    }}
                    h1 {{
                        font-size: 22px;
                        font-weight: 900;
                        margin: 0 0 10px 0;
                        color: #0f172a;
                    }}
                    p {{
                        font-size: 14px;
                        color: #64748b;
                        line-height: 1.5;
                        margin: 0 0 28px 0;
                    }}
                    .btn-primary {{
                        display: block;
                        width: 100%;
                        padding: 14px;
                        background: linear-gradient(90deg, #ED6706 0%, #ff832b 100%);
                        color: #ffffff;
                        font-weight: 800;
                        font-size: 15px;
                        text-decoration: none;
                        border-radius: 12px;
                        box-sizing: border-box;
                        box-shadow: 0 10px 15px -3px rgba(237, 103, 6, 0.35);
                        transition: transform 0.15s ease;
                        margin-bottom: 12px;
                    }}
                    .btn-primary:hover {{
                        transform: translateY(-2px);
                    }}
                    .btn-secondary {{
                        display: block;
                        width: 100%;
                        padding: 12px;
                        background: #f1f5f9;
                        color: #053679;
                        font-weight: 700;
                        font-size: 13px;
                        text-decoration: none;
                        border-radius: 12px;
                        box-sizing: border-box;
                        border: 1px solid #cbd5e1;
                        transition: background 0.15s ease;
                        margin-bottom: 8px;
                    }}
                    .btn-secondary:hover {{
                        background: #e2e8f0;
                    }}
                    .footer-note {{
                        margin-top: 24px;
                        font-size: 11px;
                        color: #94a3b8;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <span class="badge"><span class="badge-dot"></span> Backend API v{settings.app_version} Online</span>
                    <h1>CRM GLOBAL CARDS + Bling</h1>
                    <p>Você acessou o endereço do <strong>Servidor de API Backend</strong> (porta 8765). Para usar o sistema com todas as telas, acesse o aplicativo web na porta 5173:</p>
                    
                    <a href="http://127.0.0.1:5173" class="btn-primary">🚀 Abrir Painel do CRM (Frontend)</a>
                    <a href="/docs" class="btn-secondary">📘 Documentação Interativa da API (Swagger /docs)</a>
                    <a href="/api/health" class="btn-secondary">🩺 Diagnóstico & Saúde dos 21 DBFs (/api/health)</a>

                    <div class="footer-note">
                        Motor Nativo dBase III+ / Zero SQL • Sincronização 100% Bling ERP v3
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        return {
            "status": "ONLINE",
            "app": settings.app_name,
            "version": settings.app_version,
            "frontend_url": "http://127.0.0.1:5173",
            "docs_url": "/docs",
            "health_url": "/api/health",
            "storage": "DBF/dBase III+ Local (Zero SQL)",
        }

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        fav_path = Path("frontend/public/favicon.ico")
        if fav_path.exists():
            return FileResponse(fav_path, media_type="image/x-icon")
        return JSONResponse(status_code=404, content={"detail": "Favicon not found"})

    @app.get("/api/health")
    def health_check():
        return {
            "status": "OK",
            "app": settings.app_name,
            "version": settings.app_version,
            "storage": "DBF/dBase III+ Local",
            "sql_used": False,
        }

    @app.post("/api/mcp")
    def mcp_root_endpoint(payload: Dict[str, Any]):
        from app.mcp.bling_mcp import BlingMCPEngine
        return BlingMCPEngine(mgr).handle_jsonrpc(payload)

    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(clients.router)
    app.include_router(contacts.router)
    app.include_router(products.router)
    app.include_router(orders.router)
    app.include_router(quotations.router)
    app.include_router(opportunities.router)
    app.include_router(activities.router)
    app.include_router(whatsapp.router)
    app.include_router(notifications.router)
    app.include_router(reports.router)
    app.include_router(suppliers.router)
    app.include_router(integrations.router)
    app.include_router(settings_route.router)
    app.include_router(search.router)
    app.include_router(ai.router)

    return app


app = create_app()

