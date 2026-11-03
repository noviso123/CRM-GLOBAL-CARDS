import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.config import settings
from app.core.logging import write_audit_log
from app.core.permissions import check_permission
from app.core.security import hash_password
from app.database.backup import BackupManager
from app.database.dbf_manager import DBFManager
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/settings", tags=["Configurações e Administração"])


class ConfigUpdateItem(BaseModel):
    GRUPO: str = "GERAL"
    CHAVE: str
    VALOR: str
    DESCRICAO: Optional[str] = ""


class UserCreateInput(BaseModel):
    NOME: str
    LOGIN: str
    EMAIL: str
    PASSWORD: str
    PERFIL: str = "VENDEDOR"
    CARGO: Optional[str] = ""
    TELEFONE: Optional[str] = ""
    DESC_MAX: float = 10.0
    SITUACAO: str = "ATIVO"


class UserUpdateInput(BaseModel):
    NOME: Optional[str] = None
    EMAIL: Optional[str] = None
    PERFIL: Optional[str] = None
    CARGO: Optional[str] = None
    TELEFONE: Optional[str] = None
    DESC_MAX: Optional[float] = None
    SITUACAO: Optional[str] = None
    NEW_PASSWORD: Optional[str] = None


class PermissionUpdateInput(BaseModel):
    ID: str
    P_VER: bool
    P_CRIAR: bool
    P_EDITAR: bool
    P_EXCLUIR: bool
    P_EXPORT: bool


class BackupCreateInput(BaseModel):
    description: str = "Backup manual via painel administrativo"


class BackupRestoreInput(BaseModel):
    backup_id: str


@router.get("")
def list_configs(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    return mgr.find_all("CONFIG", sort_by="GRUPO")


@router.put("")
def upsert_config(
    payload: ConfigUpdateItem,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    existing = mgr.find_by_field("CONFIG", "CHAVE", payload.CHAVE.upper())
    if existing:
        rec = mgr.update(
            "CONFIG",
            existing[0]["ID"],
            {
                "GRUPO": payload.GRUPO.upper(),
                "VALOR": payload.VALOR,
                "DESCRICAO": payload.DESCRICAO or existing[0].get("DESCRICAO", ""),
                "ID_USUARIO": user["ID"],
            },
        )
        return rec or existing[0]
    return mgr.insert(
        "CONFIG",
        {
            "GRUPO": payload.GRUPO.upper(),
            "CHAVE": payload.CHAVE.upper(),
            "VALOR": payload.VALOR,
            "DESCRICAO": payload.DESCRICAO or "",
            "ID_USUARIO": user["ID"],
        },
    )


@router.get("/users")
def list_users(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    rows = mgr.find_all("USUARIOS", sort_by="NOME")
    return [AuthService.sanitize_user(u) for u in rows]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "create")
    rec = mgr.insert(
        "USUARIOS",
        {
            "NOME": payload.NOME,
            "LOGIN": payload.LOGIN,
            "EMAIL": payload.EMAIL,
            "SENHA_HASH": hash_password(payload.PASSWORD),
            "PERFIL": payload.PERFIL.upper(),
            "CARGO": payload.CARGO or "",
            "TELEFONE": payload.TELEFONE or "",
            "DESC_MAX": payload.DESC_MAX,
            "TENT_INV": 0,
            "SITUACAO": payload.SITUACAO.upper(),
        },
    )
    write_audit_log("CREATE_USER", "USUARIOS", rec["ID"], user["ID"])
    return AuthService.sanitize_user(rec)


@router.put("/users/{target_user_id}")
def update_user(
    target_user_id: str,
    payload: UserUpdateInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    changes = payload.model_dump(exclude_unset=True, exclude={"NEW_PASSWORD"})
    if payload.NEW_PASSWORD:
        changes["SENHA_HASH"] = hash_password(payload.NEW_PASSWORD)
        changes["TENT_INV"] = 0
        changes["BLOQ_ATE"] = ""
    updated = mgr.update("USUARIOS", target_user_id, changes)
    return AuthService.sanitize_user(updated or {})


@router.get("/permissions")
def list_permissions(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    return mgr.find_all("PERMISSO", sort_by="PERFIL")


@router.put("/permissions")
def update_permission_row(
    payload: PermissionUpdateInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    updated = mgr.update(
        "PERMISSO",
        payload.ID,
        {
            "P_VER": payload.P_VER,
            "P_CRIAR": payload.P_CRIAR,
            "P_EDITAR": payload.P_EDITAR,
            "P_EXCLUIR": payload.P_EXCLUIR,
            "P_EXPORT": payload.P_EXPORT,
        },
    )
    return updated or {}


@router.get("/backup/list")
def list_backups(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    return BackupManager(mgr).list_backups()


@router.post("/backup/create", status_code=status.HTTP_201_CREATED)
def create_backup(
    payload: BackupCreateInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    res = BackupManager(mgr).create_backup(description=payload.description)
    safe = dict(res)
    safe.pop("zip_path", None)
    write_audit_log("BACKUP_CREATED", "SISTEMA", res["backup_id"], user["ID"])
    return safe


@router.post("/backup/restore")
def restore_backup(
    payload: BackupRestoreInput,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    res = BackupManager(mgr).restore_backup(payload.backup_id)
    write_audit_log("BACKUP_RESTORED", "SISTEMA", payload.backup_id, user["ID"])
    return res


@router.get("/diagnostics/verify-dbf")
def verify_dbf_diagnostics(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    report = mgr.verify_all_tables_integrity()
    return {
        "engine": "GlobalCardsDBFEngine dBase III+ (0x03)",
        "sql_dependencies": False,
        "tables_count": len(report),
        "tables": report,
    }


@router.post("/diagnostics/rebuild-indexes")
def rebuild_all_indexes(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "CONFIGURACOES", "edit")
    counts = mgr.rebuild_all_indexes()
    write_audit_log("REBUILD_INDEXES", "SISTEMA", "ALL_21_TABLES", user["ID"])
    return {"status": "REBUILT", "active_records": counts}


@router.get("/audit-logs")
def get_audit_logs(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    audit_file = settings.logs_dir / "audit.jsonl"
    entries: List[Dict[str, Any]] = []
    if audit_file.exists():
        lines = audit_file.read_text(encoding="utf-8").splitlines()[-100:]
        for ln in reversed(lines):
            try:
                entries.append(json.loads(ln))
            except Exception:
                continue
    historic = mgr.find_all("HISTORIC", sort_by="DT_CRIA", descending=True)[:100]
    return {"audit_entries": entries, "commercial_history": historic}

