from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.contact import ContactCreate, ContactUpdate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso


class ContactService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)

    def create_contact(self, data: ContactCreate, user_id: str = "SYSTEM") -> Dict[str, Any]:
        payload = data.model_dump()
        self.integrity.validate_contact_insert(payload)
        payload["ID_RESP"] = data.ID_RESP or user_id
        payload["DT_ULT_INT"] = now_iso()
        rec = self.mgr.insert("CONTATOS", payload)
        self.mgr.update("CLIENTES", data.ID_CLIENTE, {"DT_ULT_INT": now_iso()})
        self.notif.record_history(
            "CONTATO",
            rec["ID"],
            "CRIACAO",
            f"Contato {rec['NOME']} ({rec.get('CARGO', '')}) vinculado ao cliente.",
            id_cliente=data.ID_CLIENTE,
            id_usuario=user_id,
        )
        return rec

    def list_contacts(
        self, client_id: Optional[str] = None, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if client_id and not search:
            return self.mgr.find_by_field("CONTATOS", "ID_CLIENTE", client_id)
        q = (search or "").strip().upper()

        def _pred(r: Dict[str, Any]) -> bool:
            if client_id and r.get("ID_CLIENTE") != client_id:
                return False
            if q:
                haystack = f"{r.get('NOME','')} {r.get('CARGO','')} {r.get('EMAIL','')} {r.get('CELULAR','')}".upper()
                if q not in haystack:
                    return False
            return True

        return self.mgr.find_all("CONTATOS", predicate=_pred, sort_by="NOME")

    def update_contact(
        self, contact_id: str, data: ContactUpdate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("CONTATOS", contact_id)
        if not curr:
            raise NotFoundErrorCRM("CONTATOS", contact_id)
        changes = data.model_dump(exclude_unset=True)
        if "ID_CLIENTE" in changes and changes["ID_CLIENTE"]:
            self.integrity.require_client(changes["ID_CLIENTE"])
        return self.mgr.update("CONTATOS", contact_id, changes) or curr

    def delete_contact(self, contact_id: str) -> bool:
        if not self.mgr.get_by_id("CONTATOS", contact_id):
            raise NotFoundErrorCRM("CONTATOS", contact_id)
        return self.mgr.delete("CONTATOS", contact_id)

