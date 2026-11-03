from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

    @app.get("/api/health")
    def health_check():
        return {
            "status": "OK",
            "app": settings.app_name,
            "version": settings.app_version,
            "storage": "DBF/dBase III+ Local",
            "sql_used": False,
        }

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
    app.include_router(integrations.router)
    app.include_router(settings_route.router)
    app.include_router(search.router)
    app.include_router(ai.router)

    return app


app = create_app()

