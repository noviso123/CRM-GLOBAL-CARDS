from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM
from app.database.dbf_manager import DBFManager
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso


class ActivityService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.notif = NotificationService(mgr)

    def create_activity(self, data: ActivityCreate, user_id: str = "SYSTEM") -> Dict[str, Any]:
        payload = data.model_dump()
        payload["ID_RESP"] = data.ID_RESP or user_id
        if not payload.get("DT_PRAZO"):
            payload["DT_PRAZO"] = f"{data.DATA_AG}T{data.HORA_AG or '18:00'}:00"
        rec = self.mgr.insert("ATIVIDAD", payload)

        if data.ID_OPORT:
            self.mgr.update(
                "OPORTUN",
                data.ID_OPORT,
                {"PROX_ATIV": f"{rec['TITULO']} ({rec['DATA_AG']})", "DT_ULT_INT": now_iso()},
            )
        if data.ID_CLIENTE:
            self.mgr.update("CLIENTES", data.ID_CLIENTE, {"DT_ULT_INT": now_iso()})
            self.notif.record_history(
                "ATIVIDADE",
                rec["ID"],
                "AGENDAMENTO",
                f"Atividade '{rec['TITULO']}' ({rec['TIPO']}) agendada para {rec['DATA_AG']}.",
                id_cliente=data.ID_CLIENTE,
                id_usuario=user_id,
            )
        return self._enrich_activity(rec)

    def _enrich_activity(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(rec)
        if rec.get("ID_CLIENTE"):
            cli = self.mgr.get_by_id("CLIENTES", rec["ID_CLIENTE"])
            item["CLIENTE_NOME"] = cli["NOME"] if cli else ""
        else:
            item["CLIENTE_NOME"] = ""
        if rec.get("ID_OPORT"):
            opp = self.mgr.get_by_id("OPORTUN", rec["ID_OPORT"])
            item["OPORTUNIDADE_TITULO"] = opp["TITULO"] if opp else ""
        else:
            item["OPORTUNIDADE_TITULO"] = ""
        return item

    def complete_activity(self, activity_id: str, user_id: str = "SYSTEM") -> Dict[str, Any]:
        curr = self.mgr.get_by_id("ATIVIDAD", activity_id)
        if not curr:
            raise NotFoundErrorCRM("ATIVIDAD", activity_id)
        updated = (
            self.mgr.update(
                "ATIVIDAD",
                activity_id,
                {"SITUACAO": "CONCLUIDA", "DT_CONCL": now_iso()},
            )
            or curr
        )
        if updated.get("ID_CLIENTE"):
            self.notif.record_history(
                "ATIVIDADE",
                activity_id,
                "CONCLUSAO",
                f"Atividade '{updated['TITULO']}' concluída.",
                id_cliente=updated["ID_CLIENTE"],
                id_usuario=user_id,
            )
        return self._enrich_activity(updated)

    def reschedule_activity(
        self, activity_id: str, new_date: str, new_time: str = "09:00", user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("ATIVIDAD", activity_id)
        if not curr:
            raise NotFoundErrorCRM("ATIVIDAD", activity_id)
        updated = (
            self.mgr.update(
                "ATIVIDAD",
                activity_id,
                {
                    "DATA_AG": new_date,
                    "HORA_AG": new_time,
                    "DT_PRAZO": f"{new_date}T{new_time}:00",
                    "SITUACAO": "PENDENTE",
                },
            )
            or curr
        )
        return self._enrich_activity(updated)

    def cancel_activity(self, activity_id: str, user_id: str = "SYSTEM") -> Dict[str, Any]:
        curr = self.mgr.get_by_id("ATIVIDAD", activity_id)
        if not curr:
            raise NotFoundErrorCRM("ATIVIDAD", activity_id)
        updated = self.mgr.update("ATIVIDAD", activity_id, {"SITUACAO": "CANCELADA"}) or curr
        return self._enrich_activity(updated)

    def update_activity(
        self, activity_id: str, data: ActivityUpdate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("ATIVIDAD", activity_id)
        if not curr:
            raise NotFoundErrorCRM("ATIVIDAD", activity_id)
        changes = data.model_dump(exclude_unset=True)
        updated = self.mgr.update("ATIVIDAD", activity_id, changes) or curr
        return self._enrich_activity(updated)

    def list_activities(
        self,
        situacao: Optional[str] = None,
        tipo: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = self.mgr.find_all("ATIVIDAD", sort_by="DATA_AG")
        out: List[Dict[str, Any]] = []
        for r in rows:
            if situacao and r.get("SITUACAO") != situacao.upper():
                continue
            if tipo and r.get("TIPO") != tipo.upper():
                continue
            if client_id and r.get("ID_CLIENTE") != client_id:
                continue
            out.append(self._enrich_activity(r))
        return out

