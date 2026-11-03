from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM, ValidationErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.order import OrderCreate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso, today_dbf


class OrderService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)

    def create_order(self, data: OrderCreate, user_id: str = "SYSTEM") -> Dict[str, Any]:
        client = self.integrity.require_client(data.ID_CLIENTE)
        numero = self.mgr.next_sequence_code("PEDIDOS", "PED")

        prepared_items: List[Dict[str, Any]] = []
        subtotal_order = 0.0
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
                raise ValidationErrorCRM(
                    f"Desconto do item ({disc}) não pode exceder o valor bruto ({gross})."
                )
            net_sub = round(gross - disc, 2)
            subtotal_order = round(subtotal_order + gross, 2)
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
                }
            )

        total_discount = round(discount_items + float(data.DESCONTO_EXTRA or 0.0), 2)
        total_final = round(subtotal_order - total_discount + float(data.FRETE or 0.0), 2)
        if total_final < 0:
            raise ValidationErrorCRM("Valor total do pedido não pode ser negativo.")

        order_rec = self.mgr.insert(
            "PEDIDOS",
            {
                "NUMERO": numero,
                "ID_CLIENTE": client["ID"],
                "ID_ORCAM": data.ID_ORCAM or "",
                "ID_OPORT": data.ID_OPORT or "",
                "DT_PEDIDO": data.DT_PEDIDO or today_dbf(),
                "SUBTOTAL": subtotal_order,
                "DESCONTO": total_discount,
                "FRETE": float(data.FRETE or 0.0),
                "TOTAL": total_final,
                "COND_PAGTO": data.COND_PAGTO or "À Vista",
                "OBS": data.OBS or "",
                "SITUACAO": data.SITUACAO or "ABERTO",
                "ORIGEM": data.ORIGEM or "LOCAL",
                "ID_RESP": user_id,
            },
        )

        saved_items: List[Dict[str, Any]] = []
        for it in prepared_items:
            it["ID_PEDIDO"] = order_rec["ID"]
            saved_items.append(self.mgr.insert("ITENS_PED", it))

        self.mgr.update("CLIENTES", client["ID"], {"DT_ULT_INT": now_iso()})
        self.notif.record_history(
            "PEDIDO",
            order_rec["ID"],
            "CRIACAO",
            f"Pedido {order_rec['NUMERO']} emitido no valor de R$ {total_final:.2f}.",
            id_cliente=client["ID"],
            id_usuario=user_id,
        )
        self.notif.notify(
            "NOVO_PEDIDO",
            f"Novo pedido {order_rec['NUMERO']}",
            f"Cliente {client['NOME']} — Total R$ {total_final:.2f}",
            entidade="PEDIDOS",
            id_ref=order_rec["ID"],
        )

        # Transmissão automática do pedido para o Bling ERP v3
        try:
            from app.integrations.bling.outbound import export_order_to_bling

            export_order_to_bling(self.mgr, order_rec, saved_items)
            order_rec = self.mgr.get_by_id("PEDIDOS", order_rec["ID"]) or order_rec
        except Exception:
            pass

        # Disparo automático de notificação no WhatsApp
        try:
            if client:
                tel = str(client.get("CELULAR") or client.get("TELEFONE") or "")
                if tel:
                    from app.integrations.whatsapp.client import WhatsAppCloudClient

                    WhatsAppCloudClient(self.mgr).send_cloud_template_message(
                        to_phone=tel,
                        template_name="confirmacao_pedido",
                        parameters=[
                            client.get("NOME", "Cliente"),
                            order_rec.get("NUMERO", ""),
                            f"{total_final:.2f}",
                        ],
                    )
        except Exception:
            pass

        return self._enrich_order(order_rec, saved_items)

    def _enrich_order(
        self, order_rec: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        result = dict(order_rec)
        cli = self.mgr.get_by_id("CLIENTES", order_rec.get("ID_CLIENTE", ""))
        result["CLIENTE_NOME"] = cli["NOME"] if cli else "Cliente não identificado"
        result["CLIENTE_CPF_CNPJ"] = cli.get("CPF_CNPJ", "") if cli else ""
        result["ITEMS"] = (
            items
            if items is not None
            else self.mgr.find_by_field("ITENS_PED", "ID_PEDIDO", order_rec["ID"])
        )
        result["HISTORY"] = self.mgr.find_by_field("HISTORIC", "ID_REG", order_rec["ID"])
        return result

    def get_order(self, order_id: str) -> Dict[str, Any]:
        rec = self.mgr.get_by_id("PEDIDOS", order_id)
        if not rec:
            raise NotFoundErrorCRM("PEDIDOS", order_id)
        return self._enrich_order(rec)

    def update_status(
        self, order_id: str, new_status: str, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("PEDIDOS", order_id)
        if not curr:
            raise NotFoundErrorCRM("PEDIDOS", order_id)
        updated = self.mgr.update("PEDIDOS", order_id, {"SITUACAO": new_status.upper()}) or curr
        self.notif.record_history(
            "PEDIDO",
            order_id,
            "MUDANCA_SITUACAO",
            f"Situação do pedido {updated['NUMERO']} alterada de {curr['SITUACAO']} para {new_status.upper()}.",
            id_cliente=updated["ID_CLIENTE"],
            id_usuario=user_id,
        )

        # Avança a situação do pedido no Bling ERP v3 automaticamente
        try:
            from app.integrations.bling.outbound import advance_order_status_in_bling

            advance_order_status_in_bling(self.mgr, order_id, new_status.upper())
        except Exception:
            pass

        # Notificação automática via WhatsApp para o cliente sobre a mudança de situação
        try:
            cli = self.mgr.get_by_id("CLIENTES", updated.get("ID_CLIENTE", ""))
            if cli:
                tel = str(cli.get("CELULAR") or cli.get("TELEFONE") or "")
                if tel:
                    from app.integrations.whatsapp.client import WhatsAppCloudClient

                    wa = WhatsAppCloudClient(self.mgr)
                    if new_status.upper() == "FATURADO":
                        wa.send_cloud_template_message(
                            to_phone=tel,
                            template_name="pedido_faturado",
                            parameters=[cli.get("NOME", "Cliente"), updated.get("NUMERO", "")],
                        )
                    elif new_status.upper() == "APROVADO":
                        wa.send_cloud_template_message(
                            to_phone=tel,
                            template_name="confirmacao_pedido",
                            parameters=[
                                cli.get("NOME", "Cliente"),
                                updated.get("NUMERO", ""),
                                f"{float(updated.get('TOTAL', 0)):.2f}",
                            ],
                        )
        except Exception:
            pass

        return self._enrich_order(updated)

    def list_orders(
        self,
        search: Optional[str] = None,
        situacao: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()
        rows = self.mgr.find_all("PEDIDOS", sort_by="DT_CRIA", descending=True)
        enriched = [self._enrich_order(r) for r in rows]
        results: List[Dict[str, Any]] = []
        for r in enriched:
            if situacao and r.get("SITUACAO") != situacao.upper():
                continue
            if client_id and r.get("ID_CLIENTE") != client_id:
                continue
            if q:
                hay = f"{r.get('NUMERO','')} {r.get('CLIENTE_NOME','')} {r.get('ID_EXT','')}".upper()
                if q not in hay:
                    continue
            results.append(r)
        return results

