from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM, ValidationErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.order import OrderCreate, OrderItemInput
from app.schemas.quotation import QuotationCreate
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.utils.dates import now_iso, today_dbf


class QuotationService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)
        self.order_svc = OrderService(mgr)

    def create_quotation(
        self, data: QuotationCreate, user_id: str = "SYSTEM", user_max_disc: float = 100.0
    ) -> Dict[str, Any]:
        client = self.integrity.require_client(data.ID_CLIENTE)
        numero = self.mgr.next_sequence_code("ORCAMENT", "ORC")

        prepared_items: List[Dict[str, Any]] = []
        subtotal_quo = 0.0
        discount_items = 0.0

        for item_in in data.ITEMS:
            prod = self.integrity.require_product(item_in.ID_PRODUTO)
            unit_price = (
                float(item_in.PRECO_UNIT)
                if item_in.PRECO_UNIT is not None
                else float(prod.get("PRECO", 0.0))
            )
            gross = round(float(item_in.QUANTIDADE) * unit_price, 2)
            disc = round(float(item_in.DESC_VALOR or 0.0), 2)
            if disc > gross:
                raise ValidationErrorCRM("Desconto do item maior que o valor bruto.")
            net_sub = round(gross - disc, 2)
            subtotal_quo = round(subtotal_quo + gross, 2)
            discount_items = round(discount_items + disc, 2)
            prepared_items.append(
                {
                    "ID_PRODUTO": prod["ID"],
                    "CODIGO_PRD": prod["CODIGO"],
                    "NOME_PRD": prod["NOME"],
                    "QUANTIDADE": float(item_in.QUANTIDADE),
                    "PRECO_UNIT": unit_price,
                    "DESC_VALOR": disc,
                    "SUBTOTAL": net_sub,
                    "OBS_ITEM": item_in.OBS_ITEM or "",
                }
            )

        total_disc = round(discount_items + float(data.DESCONTO_EXTRA or 0.0), 2)
        disc_perc = round((total_disc / subtotal_quo) * 100.0, 2) if subtotal_quo > 0 else 0.0
        total_final = round(subtotal_quo - total_disc + float(data.FRETE or 0.0), 2)

        aut_desc = disc_perc <= user_max_disc
        dt_valid = data.DT_VALID or (date.today() + timedelta(days=15)).strftime("%Y%m%d")

        quo_rec = self.mgr.insert(
            "ORCAMENT",
            {
                "NUMERO": numero,
                "ID_CLIENTE": client["ID"],
                "ID_CONTATO": data.ID_CONTATO or "",
                "ID_OPORT": data.ID_OPORT or "",
                "DT_EMISSAO": data.DT_EMISSAO or today_dbf(),
                "DT_VALID": dt_valid,
                "SUBTOTAL": subtotal_quo,
                "DESCONTO": total_disc,
                "DESC_PERC": disc_perc,
                "FRETE": float(data.FRETE or 0.0),
                "TOTAL": total_final,
                "AUT_DESC": aut_desc,
                "ID_APROV": user_id if aut_desc else "",
                "OBS": data.OBS or "",
                "SITUACAO": data.SITUACAO or "EM_ELABORACAO",
                "ORIGEM": "OPORTUNIDADE" if data.ID_OPORT else "LOCAL",
                "ID_RESP": user_id,
            },
        )

        saved_items: List[Dict[str, Any]] = []
        for it in prepared_items:
            it["ID_ORCAM"] = quo_rec["ID"]
            saved_items.append(self.mgr.insert("ITENS_ORC", it))

        self.mgr.update("CLIENTES", client["ID"], {"DT_ULT_INT": now_iso()})
        self.notif.record_history(
            "ORCAMENTO",
            quo_rec["ID"],
            "CRIACAO",
            f"Orçamento {quo_rec['NUMERO']} criado no valor de R$ {total_final:.2f}.",
            id_cliente=client["ID"],
            id_usuario=user_id,
        )
        self.notif.notify(
            "NOVO_ORCAMENTO",
            f"Orçamento {quo_rec['NUMERO']} gerado",
            f"Cliente {client['NOME']} — R$ {total_final:.2f}",
            entidade="ORCAMENTOS",
            id_ref=quo_rec["ID"],
        )
        return self._enrich_quotation(quo_rec, saved_items)

    def _enrich_quotation(
        self, quo_rec: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        result = dict(quo_rec)
        cli = self.mgr.get_by_id("CLIENTES", quo_rec.get("ID_CLIENTE", ""))
        result["CLIENTE_NOME"] = cli["NOME"] if cli else ""
        result["ITEMS"] = (
            items
            if items is not None
            else self.mgr.find_by_field("ITENS_ORC", "ID_ORCAM", quo_rec["ID"])
        )
        result["HISTORY"] = self.mgr.find_by_field("HISTORIC", "ID_REG", quo_rec["ID"])
        return result

    def get_quotation(self, quotation_id: str) -> Dict[str, Any]:
        rec = self.mgr.get_by_id("ORCAMENT", quotation_id)
        if not rec:
            raise NotFoundErrorCRM("ORCAMENT", quotation_id)
        return self._enrich_quotation(rec)

    def update_status(
        self, quotation_id: str, new_status: str, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("ORCAMENT", quotation_id)
        if not curr:
            raise NotFoundErrorCRM("ORCAMENT", quotation_id)
        st = new_status.upper()
        updates: Dict[str, Any] = {"SITUACAO": st}
        if st == "APROVADO":
            updates["AUT_DESC"] = True
            updates["ID_APROV"] = user_id
        updated = self.mgr.update("ORCAMENT", quotation_id, updates) or curr
        self.notif.record_history(
            "ORCAMENTO",
            quotation_id,
            "MUDANCA_SITUACAO",
            f"Orçamento {updated['NUMERO']} alterado para {st}.",
            id_cliente=updated["ID_CLIENTE"],
            id_usuario=user_id,
        )
        return self._enrich_quotation(updated)

    def convert_to_order(
        self, quotation_id: str, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        quo = self.get_quotation(quotation_id)
        if quo.get("SITUACAO") == "CONVERTIDO" and quo.get("ID_PED_GER"):
            return self.order_svc.get_order(quo["ID_PED_GER"])
        if quo.get("SITUACAO") in ("REPROVADO", "EXPIRADO"):
            raise ValidationErrorCRM("Orçamento reprovado ou expirado não pode ser convertido em pedido.")

        order_items = [
            OrderItemInput(
                ID_PRODUTO=it["ID_PRODUTO"],
                QUANTIDADE=float(it["QUANTIDADE"]),
                PRECO_UNIT=float(it["PRECO_UNIT"]),
                DESC_VALOR=float(it["DESC_VALOR"]),
            )
            for it in quo["ITEMS"]
        ]
        order = self.order_svc.create_order(
            OrderCreate(
                ID_CLIENTE=quo["ID_CLIENTE"],
                ID_ORCAM=quo["ID"],
                ID_OPORT=quo.get("ID_OPORT", ""),
                FRETE=float(quo.get("FRETE", 0.0)),
                OBS=f"Convertido do orçamento {quo['NUMERO']}. {quo.get('OBS', '')}".strip(),
                SITUACAO="APROVADO",
                ORIGEM="ORCAMENTO",
                ITEMS=order_items,
            ),
            user_id=user_id,
        )
        self.mgr.update(
            "ORCAMENT",
            quotation_id,
            {"SITUACAO": "CONVERTIDO", "ID_PED_GER": order["ID"]},
        )
        self.notif.record_history(
            "ORCAMENTO",
            quotation_id,
            "CONVERSAO_PEDIDO",
            f"Orçamento {quo['NUMERO']} convertido no pedido {order['NUMERO']}.",
            id_cliente=quo["ID_CLIENTE"],
            id_usuario=user_id,
        )
        return order

    def list_quotations(
        self,
        search: Optional[str] = None,
        situacao: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()
        rows = self.mgr.find_all("ORCAMENT", sort_by="DT_CRIA", descending=True)
        enriched = [self._enrich_quotation(r) for r in rows]
        out: List[Dict[str, Any]] = []
        for r in enriched:
            if situacao and r.get("SITUACAO") != situacao.upper():
                continue
            if client_id and r.get("ID_CLIENTE") != client_id:
                continue
            if q and q not in f"{r.get('NUMERO','')} {r.get('CLIENTE_NOME','')}".upper():
                continue
            out.append(r)
        return out

