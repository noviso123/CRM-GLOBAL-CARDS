from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM, ValidationErrorCRM
from app.core.logging import write_audit_log
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.client import AddressCreate, ClientCreate, ClientUpdate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso
from app.utils.files import load_external_document, save_external_document
from app.utils.validators import normalize_digits, validate_cpf_cnpj, validate_email


class ClientService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)

    def create_client(self, data: ClientCreate, user_id: str = "SYSTEM") -> Dict[str, Any]:
        if data.CPF_CNPJ and not validate_cpf_cnpj(data.CPF_CNPJ):
            raise ValidationErrorCRM("CPF ou CNPJ inválido.")
        if data.EMAIL and not validate_email(data.EMAIL):
            raise ValidationErrorCRM("Endereço de e-mail inválido.")

        codigo = data.CODIGO or self.mgr.next_sequence_code("CLIENTES", "CLI")
        cpf_cnpj_norm = normalize_digits(data.CPF_CNPJ) if data.CPF_CNPJ else ""
        if cpf_cnpj_norm:
            existing_doc = self.mgr.find_by_field("CLIENTES", "CPF_CNPJ", cpf_cnpj_norm)
            if existing_doc:
                raise ValidationErrorCRM(f"Já existe cliente cadastrado com o CPF/CNPJ {data.CPF_CNPJ}.")

        payload = data.model_dump(exclude={"OBSERVACOES_LONGAS"})
        payload["CODIGO"] = codigo
        payload["CPF_CNPJ"] = cpf_cnpj_norm
        payload["ID_RESP"] = data.ID_RESP or user_id
        payload["DT_ULT_INT"] = now_iso()

        rec = self.mgr.insert("CLIENTES", payload)
        if data.OBSERVACOES_LONGAS:
            doc_ref = save_external_document(
                self.mgr.base_dir,
                "clients",
                rec["ID"],
                {"content": data.OBSERVACOES_LONGAS, "updated_at": now_iso()},
            )
            rec = self.mgr.update("CLIENTES", rec["ID"], {"DOC_REF": doc_ref}) or rec

        self.notif.record_history(
            "CLIENTE",
            rec["ID"],
            "CRIACAO",
            f"Cliente {rec['NOME']} ({rec['CODIGO']}) cadastrado.",
            id_cliente=rec["ID"],
            id_usuario=user_id,
        )
        self.notif.notify(
            "NOVO_CLIENTE",
            "Novo cliente cadastrado",
            f"{rec['NOME']} ({rec['CODIGO']}) foi adicionado à base.",
            entidade="CLIENTES",
            id_ref=rec["ID"],
        )
        write_audit_log("CREATE", "CLIENTES", rec["ID"], user_id)
        return rec

    def get_client(self, client_id: str) -> Dict[str, Any]:
        rec = self.mgr.get_by_id("CLIENTES", client_id)
        if not rec:
            raise NotFoundErrorCRM("CLIENTES", client_id)
        return rec

    def update_client(
        self, client_id: str, data: ClientUpdate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        current = self.get_client(client_id)
        changes = data.model_dump(exclude_unset=True, exclude={"OBSERVACOES_LONGAS"})
        if "CPF_CNPJ" in changes and changes["CPF_CNPJ"]:
            if not validate_cpf_cnpj(changes["CPF_CNPJ"]):
                raise ValidationErrorCRM("CPF ou CNPJ inválido.")
            changes["CPF_CNPJ"] = normalize_digits(changes["CPF_CNPJ"])
        if "EMAIL" in changes and changes["EMAIL"] and not validate_email(changes["EMAIL"]):
            raise ValidationErrorCRM("E-mail inválido.")

        if data.OBSERVACOES_LONGAS is not None:
            doc_ref = save_external_document(
                self.mgr.base_dir,
                "clients",
                client_id,
                {"content": data.OBSERVACOES_LONGAS, "updated_at": now_iso()},
            )
            changes["DOC_REF"] = doc_ref

        updated = self.mgr.update("CLIENTES", client_id, changes) or current
        self.notif.record_history(
            "CLIENTE",
            client_id,
            "ATUALIZACAO",
            f"Dados cadastrais do cliente {updated['NOME']} atualizados.",
            id_cliente=client_id,
            id_usuario=user_id,
        )
        write_audit_log("UPDATE", "CLIENTES", client_id, user_id)
        return updated

    def delete_client(self, client_id: str, user_id: str = "SYSTEM") -> bool:
        self.integrity.check_client_can_be_deleted(client_id)
        res = self.mgr.delete("CLIENTES", client_id)
        write_audit_log("DELETE", "CLIENTES", client_id, user_id)
        return res

    def add_address(
        self, client_id: str, data: AddressCreate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        self.get_client(client_id)
        payload = data.model_dump()
        payload["ID_CLIENTE"] = client_id
        addr = self.mgr.insert("ENDERECOS", payload)
        self.notif.record_history(
            "CLIENTE",
            client_id,
            "NOVO_ENDERECO",
            f"Endereço ({addr['TIPO_END']}) adicionado em {addr['CIDADE']}/{addr['UF']}.",
            id_cliente=client_id,
            id_usuario=user_id,
        )
        return addr

    def get_client_overview_10_tabs(self, client_id: str) -> Dict[str, Any]:
        client = self.get_client(client_id)
        contacts = self.mgr.find_by_field("CONTATOS", "ID_CLIENTE", client_id)
        addresses = self.mgr.find_by_field("ENDERECOS", "ID_CLIENTE", client_id)
        orders = self.mgr.find_by_field("PEDIDOS", "ID_CLIENTE", client_id)
        quotations = self.mgr.find_by_field("ORCAMENT", "ID_CLIENTE", client_id)
        opportunities = self.mgr.find_by_field("OPORTUN", "ID_CLIENTE", client_id)
        conversations = self.mgr.find_by_field("CONVERS", "ID_CLIENTE", client_id)
        activities = self.mgr.find_by_field("ATIVIDAD", "ID_CLIENTE", client_id)
        history = self.mgr.find_by_field("HISTORIC", "ID_CLIENTE", client_id)
        history.sort(key=lambda r: r.get("DT_CRIA", ""), reverse=True)
        notes = load_external_document(self.mgr.base_dir, client.get("DOC_REF"))
        if not notes and client.get("OBS_CURTA"):
            notes = {"content": client.get("OBS_CURTA"), "updated_at": client.get("DT_ATUA")}

        return {
            "client": client,
            "contacts": contacts,
            "addresses": addresses,
            "orders": orders,
            "quotations": quotations,
            "opportunities": opportunities,
            "conversations": conversations,
            "activities": activities,
            "history": history,
            "notes": notes,
        }

    def list_clients(
        self,
        search: Optional[str] = None,
        situacao: Optional[str] = None,
        uf: Optional[str] = None,
        origem: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()

        def _pred(r: Dict[str, Any]) -> bool:
            if situacao and r.get("SITUACAO") != situacao.upper():
                return False
            if uf and r.get("UF") != uf.upper():
                return False
            if origem and r.get("ORIGEM") != origem.upper():
                return False
            if q:
                haystack = " ".join(
                    str(r.get(k, ""))
                    for k in ("CODIGO", "NOME", "FANTASIA", "CPF_CNPJ", "EMAIL", "TELEFONE", "CELULAR", "CIDADE")
                ).upper()
                if q not in haystack:
                    return False
            return True

        return self.mgr.find_all("CLIENTES", predicate=_pred, sort_by="DT_CRIA", descending=True)

