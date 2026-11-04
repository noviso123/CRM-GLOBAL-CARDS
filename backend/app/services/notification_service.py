from typing import Any, Dict, List, Optional
from app.database.dbf_manager import DBFManager
from app.utils.dates import now_iso


class NotificationService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr

    def notify(
        self,
        tipo: str,
        titulo: str,
        mensagem: str,
        entidade: str = "",
        id_ref: str = "",
        id_usu_dst: str = "TODOS",
    ) -> Dict[str, Any]:
        return self.mgr.insert(
            "NOTIFIC",
            {
                "ID_USU_DST": id_usu_dst or "TODOS",
                "TIPO": tipo[:25],
                "TITULO": titulo[:100],
                "MENSAGEM": mensagem[:220],
                "ENTIDADE": entidade[:20],
                "ID_REF": id_ref[:36],
                "LIDA": False,
            },
        )

    def list_notifications(
        self, user_id: str, unread_only: bool = False, tipo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        def _pred(r: Dict[str, Any]) -> bool:
            if r.get("ID_USU_DST") not in ("TODOS", "", user_id):
                return False
            if unread_only and r.get("LIDA"):
                return False
            if tipo and r.get("TIPO") != tipo.upper():
                return False
            return True

        return self.mgr.find_all("NOTIFIC", predicate=_pred, sort_by="DT_CRIA", descending=True)

    def mark_read(self, notification_id: str) -> Optional[Dict[str, Any]]:
        return self.mgr.update(
            "NOTIFIC", notification_id, {"LIDA": True, "DT_LEITURA": now_iso()}
        )

    def mark_all_read(self, user_id: str) -> int:
        unread = self.list_notifications(user_id=user_id, unread_only=True)
        count = 0
        for n in unread:
            self.mark_read(n["ID"])
            count += 1
        return count

    def delete_notification(self, notification_id: str) -> bool:
        ok = self.mgr.delete("NOTIFIC", notification_id)
        if ok:
            try:
                self.mgr.pack_table("NOTIFIC")
            except Exception:
                pass
        return ok

    def clear_all(self, user_id: str) -> int:
        all_notifs = self.list_notifications(user_id=user_id, unread_only=False)
        count = 0
        for n in all_notifs:
            if self.mgr.delete("NOTIFIC", n["ID"]):
                count += 1
        if count > 0:
            try:
                self.mgr.pack_table("NOTIFIC")
            except Exception:
                pass
        return count

    def record_history(
        self,
        entidade: str,
        id_reg: str,
        acao: str,
        descricao: str,
        id_cliente: str = "",
        id_usuario: str = "SYSTEM",
    ) -> Dict[str, Any]:
        return self.mgr.insert(
            "HISTORIC",
            {
                "ENTIDADE": entidade[:20],
                "ID_REG": id_reg[:36],
                "ID_CLIENTE": id_cliente[:36],
                "ACAO": acao[:30],
                "DESCRICAO": descricao[:250],
                "ID_USUARIO": id_usuario[:36],
            },
        )

