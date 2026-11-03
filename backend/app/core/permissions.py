from typing import Any, Dict, List
from app.core.exceptions import PermissionDeniedErrorCRM
from app.database.dbf_manager import DBFManager


def get_user_permissions(mgr: DBFManager, perfil: str) -> Dict[str, Dict[str, bool]]:
    rows: List[Dict[str, Any]] = mgr.find_by_field("PERMISSO", "PERFIL", perfil.upper())
    matrix: Dict[str, Dict[str, bool]] = {}
    for r in rows:
        mod = r.get("MODULO", "")
        matrix[mod] = {
            "view": bool(r.get("P_VER", True)),
            "create": bool(r.get("P_CRIAR", False)),
            "edit": bool(r.get("P_EDITAR", False)),
            "delete": bool(r.get("P_EXCLUIR", False)),
            "export": bool(r.get("P_EXPORT", False)),
        }
    return matrix


def check_permission(
    mgr: DBFManager, user: Dict[str, Any], module: str, action: str = "view"
) -> None:
    perfil = str(user.get("PERFIL", "VENDEDOR")).upper()
    if perfil == "ADMIN":
        return
    matrix = get_user_permissions(mgr, perfil)
    mod_perms = matrix.get(module.upper())
    if not mod_perms or not mod_perms.get(action, False):
        raise PermissionDeniedErrorCRM(
            f"Seu perfil ({perfil}) não possui permissão '{action}' no módulo {module}."
        )

