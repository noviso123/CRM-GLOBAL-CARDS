from typing import Any, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import get_user_permissions
from app.database.dbf_manager import DBFManager
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    login: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RecoverPasswordRequest(BaseModel):
    email: str


@router.post("/login")
def login(payload: LoginRequest, mgr: DBFManager = Depends(get_dbf_manager)) -> Dict[str, Any]:
    svc = AuthService(mgr)
    return svc.authenticate(payload.login, payload.password)


@router.post("/logout")
def logout(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {"status": "LOGGED_OUT", "user_id": user["ID"]}


@router.get("/me")
def get_me(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    perms = get_user_permissions(mgr, user.get("PERFIL", "VENDEDOR"))
    return {"user": AuthService.sanitize_user(user), "permissions": perms}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    svc = AuthService(mgr)
    updated = svc.change_password(user["ID"], payload.current_password, payload.new_password)
    return {"status": "PASSWORD_UPDATED", "user": updated}


@router.post("/recover-password")
def recover_password(
    payload: RecoverPasswordRequest, mgr: DBFManager = Depends(get_dbf_manager)
) -> Dict[str, Any]:
    matches = mgr.find_by_field("USUARIOS", "EMAIL", payload.email.strip())
    return {
        "status": "RECOVERY_REGISTERED",
        "message": "Caso o e-mail pertença a um usuário ativo, solicite ao Administrador Local a redefinição nas Configurações.",
        "found": bool(matches),
    }

