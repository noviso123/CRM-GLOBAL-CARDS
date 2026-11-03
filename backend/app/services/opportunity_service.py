from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM, ValidationErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate, StageCreate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso


class OpportunityService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)

    def list_funnels_with_stages(self) -> List[Dict[str, Any]]:
        funnels = self.mgr.find_all("FUNIL", sort_by="DT_CRIA")
        out: List[Dict[str, Any]] = []
        for f in funnels:
            stages = self.mgr.find_by_field("ETAPAS", "ID_FUNIL", f["ID"])
            stages.sort(key=lambda s: int(s.get("ORDEM", 1)))
            f_copy = dict(f)
            f_copy["stages"] = stages
            out.append(f_copy)
        return out

    def create_stage(self, data: StageCreate) -> Dict[str, Any]:
        if not self.mgr.get_by_id("FUNIL", data.ID_FUNIL):
            raise NotFoundErrorCRM("FUNIL", data.ID_FUNIL)
        return self.mgr.insert("ETAPAS", data.model_dump())

    def update_stage(self, stage_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        stage = self.mgr.get_by_id("ETAPAS", stage_id)
        if not stage:
            raise NotFoundErrorCRM("ETAPAS", stage_id)
        return self.mgr.update("ETAPAS", stage_id, changes) or stage

    def create_opportunity(
        self, data: OpportunityCreate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        cli = self.integrity.require_client(data.ID_CLIENTE)
        funnels = self.list_funnels_with_stages()
        funnel_id = data.ID_FUNIL or (funnels[0]["ID"] if funnels else "")
        stages = self.mgr.find_by_field("ETAPAS", "ID_FUNIL", funnel_id)
        stages.sort(key=lambda s: int(s.get("ORDEM", 1)))
        stage_id = data.ID_ETAPA or (stages[0]["ID"] if stages else "")
        stage_obj = self.mgr.get_by_id("ETAPAS", stage_id)
        prob = (
            float(data.PROBABIL)
            if data.PROBABIL is not None
            else (float(stage_obj.get("PROB_PAD", 20.0)) if stage_obj else 20.0)
        )

        payload = data.model_dump()
        payload["ID_FUNIL"] = funnel_id
        payload["ID_ETAPA"] = stage_id
        payload["PROBABIL"] = prob
        payload["ID_RESP"] = data.ID_RESP or user_id
        payload["DT_ULT_INT"] = now_iso()
        payload["SITUACAO"] = stage_obj.get("TIPO_ETAPA", "ABERTA") if stage_obj else "ABERTA"

        rec = self.mgr.insert("OPORTUN", payload)
        self.mgr.update("CLIENTES", cli["ID"], {"DT_ULT_INT": now_iso()})
        self.notif.record_history(
            "OPORTUNIDADE",
            rec["ID"],
            "CRIACAO",
            f"Oportunidade '{rec['TITULO']}' criada na etapa {stage_obj['NOME'] if stage_obj else ''}.",
            id_cliente=cli["ID"],
            id_usuario=user_id,
        )
        self.notif.notify(
            "OPORTUNIDADE",
            "Nova oportunidade criada",
            f"{rec['TITULO']} — Cliente {cli['NOME']} (R$ {rec['VALOR_EST']:.2f})",
            entidade="OPORTUNIDADES",
            id_ref=rec["ID"],
        )
        return self._enrich_opportunity(rec)

    def _enrich_opportunity(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(rec)
        cli = self.mgr.get_by_id("CLIENTES", rec.get("ID_CLIENTE", ""))
        stage = self.mgr.get_by_id("ETAPAS", rec.get("ID_ETAPA", ""))
        item["CLIENTE_NOME"] = cli["NOME"] if cli else ""
        item["ETAPA_NOME"] = stage["NOME"] if stage else ""
        item["ETAPA_COR"] = stage.get("COR", "#0284C7") if stage else "#0284C7"
        item["history"] = self.mgr.find_by_field("HISTORIC", "ID_REG", rec["ID"])
        return item

    def get_opportunity(self, opp_id: str) -> Dict[str, Any]:
        rec = self.mgr.get_by_id("OPORTUN", opp_id)
        if not rec:
            raise NotFoundErrorCRM("OPORTUN", opp_id)
        return self._enrich_opportunity(rec)

    def move_stage(
        self,
        opp_id: str,
        new_stage_id: str,
        motivo_perda: Optional[str] = None,
        user_id: str = "SYSTEM",
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("OPORTUN", opp_id)
        if not curr:
            raise NotFoundErrorCRM("OPORTUN", opp_id)
        old_stage = self.mgr.get_by_id("ETAPAS", curr.get("ID_ETAPA", ""))
        new_stage = self.mgr.get_by_id("ETAPAS", new_stage_id)
        if not new_stage:
            raise NotFoundErrorCRM("ETAPAS", new_stage_id)

        tipo_etapa = new_stage.get("TIPO_ETAPA", "ABERTA")
        if tipo_etapa == "PERDIDA" and not (motivo_perda or curr.get("MOT_PERDA")):
            motivo_perda = "Não especificado"

        updates: Dict[str, Any] = {
            "ID_ETAPA": new_stage_id,
            "PROBABIL": float(new_stage.get("PROB_PAD", curr.get("PROBABIL", 20.0))),
            "SITUACAO": tipo_etapa,
            "DT_ULT_INT": now_iso(),
        }
        if motivo_perda:
            updates["MOT_PERDA"] = motivo_perda

        updated = self.mgr.update("OPORTUN", opp_id, updates) or curr
        self.mgr.update("CLIENTES", updated["ID_CLIENTE"], {"DT_ULT_INT": now_iso()})
        self.notif.record_history(
            "OPORTUNIDADE",
            opp_id,
            "MUDANCA_ETAPA",
            f"Etapa alterada de '{old_stage['NOME'] if old_stage else ''}' para '{new_stage['NOME']}'.",
            id_cliente=updated["ID_CLIENTE"],
            id_usuario=user_id,
        )
        return self._enrich_opportunity(updated)

    def update_opportunity(
        self, opp_id: str, data: OpportunityUpdate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("OPORTUN", opp_id)
        if not curr:
            raise NotFoundErrorCRM("OPORTUN", opp_id)
        changes = data.model_dump(exclude_unset=True)
        if "ID_ETAPA" in changes and changes["ID_ETAPA"] != curr.get("ID_ETAPA"):
            return self.move_stage(
                opp_id,
                changes["ID_ETAPA"],
                motivo_perda=changes.get("MOT_PERDA"),
                user_id=user_id,
            )
        updated = self.mgr.update("OPORTUN", opp_id, changes) or curr
        self.notif.record_history(
            "OPORTUNIDADE",
            opp_id,
            "ATUALIZACAO",
            f"Oportunidade '{updated['TITULO']}' atualizada.",
            id_cliente=updated["ID_CLIENTE"],
            id_usuario=user_id,
        )
        return self._enrich_opportunity(updated)

    def list_opportunities(
        self,
        funnel_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        situacao: Optional[str] = None,
        client_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()
        rows = self.mgr.find_all("OPORTUN", sort_by="DT_ATUA", descending=True)
        enriched = [self._enrich_opportunity(r) for r in rows]
        out: List[Dict[str, Any]] = []
        for r in enriched:
            if funnel_id and r.get("ID_FUNIL") != funnel_id:
                continue
            if stage_id and r.get("ID_ETAPA") != stage_id:
                continue
            if situacao and r.get("SITUACAO") != situacao.upper():
                continue
            if client_id and r.get("ID_CLIENTE") != client_id:
                continue
            if q and q not in f"{r.get('TITULO','')} {r.get('CLIENTE_NOME','')}".upper():
                continue
            out.append(r)
        return out

