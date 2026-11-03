from datetime import datetime, timedelta
from typing import Any, Dict
from app.core.config import settings
from app.core.exceptions import AuthenticationErrorCRM, NotFoundErrorCRM, ValidationErrorCRM
from app.core.logging import write_audit_log
from app.core.permissions import get_user_permissions
from app.core.security import create_access_token, hash_password, verify_password
from app.database.dbf_manager import DBFManager
from app.utils.dates import now_iso


class AuthService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr

    @staticmethod
    def sanitize_user(user: Dict[str, Any]) -> Dict[str, Any]:
        safe = dict(user)
        safe.pop("SENHA_HASH", None)
        return safe

    def authenticate(self, login_or_email: str, password: str) -> Dict[str, Any]:
        identifier = login_or_email.strip()
        matches = self.mgr.find_by_field("USUARIOS", "LOGIN", identifier)
        if not matches:
            matches = self.mgr.find_by_field("USUARIOS", "EMAIL", identifier)
        if not matches:
            write_audit_log("LOGIN_FAILED", "USUARIOS", identifier, result="NOT_FOUND")
            raise AuthenticationErrorCRM("Usuário ou senha inválidos.")

        user = matches[0]
        if user.get("SITUACAO") != "ATIVO":
            raise AuthenticationErrorCRM("Conta de usuário inativa ou bloqueada.")

        bloq_ate = user.get("BLOQ_ATE", "")
        if bloq_ate:
            try:
                lock_dt = datetime.strptime(bloq_ate, "%Y-%m-%dT%H:%M:%S")
                if datetime.now() < lock_dt:
                    raise AuthenticationErrorCRM(
                        f"Conta temporariamente bloqueada por tentativas inválidas até {bloq_ate}."
                    )
            except ValueError:
                pass

        if not verify_password(password, user.get("SENHA_HASH", "")):
            attempts = int(user.get("TENT_INV", 0)) + 1
            updates: Dict[str, Any] = {"TENT_INV": attempts}
            if attempts >= settings.max_login_attempts:
                until = (
                    datetime.now() + timedelta(minutes=settings.lockout_minutes)
                ).strftime("%Y-%m-%dT%H:%M:%S")
                updates["BLOQ_ATE"] = until
            self.mgr.update("USUARIOS", user["ID"], updates)
            write_audit_log("LOGIN_FAILED", "USUARIOS", user["ID"], user["ID"], result="BAD_PASSWORD")
            raise AuthenticationErrorCRM("Usuário ou senha inválidos.")

        updated_user = self.mgr.update(
            "USUARIOS",
            user["ID"],
            {"TENT_INV": 0, "BLOQ_ATE": "", "ULT_LOGIN": now_iso()},
        ) or user

        token = create_access_token(
            subject=updated_user["ID"],
            extra_claims={"perfil": updated_user["PERFIL"], "login": updated_user["LOGIN"]},
        )
        permissions = get_user_permissions(self.mgr, updated_user["PERFIL"])
        write_audit_log("LOGIN_SUCCESS", "USUARIOS", updated_user["ID"], updated_user["ID"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": self.sanitize_user(updated_user),
            "permissions": permissions,
        }

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        user = self.mgr.get_by_id("USUARIOS", user_id)
        if not user:
            raise NotFoundErrorCRM("USUARIOS", user_id)
        if not verify_password(current_password, user.get("SENHA_HASH", "")):
            raise AuthenticationErrorCRM("Senha atual incorreta.")
        if len(new_password) < 6:
            raise ValidationErrorCRM("A nova senha deve ter no mínimo 6 caracteres.")
        updated = self.mgr.update(
            "USUARIOS", user_id, {"SENHA_HASH": hash_password(new_password)}
        )
        write_audit_log("PASSWORD_CHANGED", "USUARIOS", user_id, user_id)
        return self.sanitize_user(updated or user)

