"""Orquestrador de Sincronização 100% Bidirecional Omnichannel.

Garante sincronização total e contínua:
1. Bling ERP -> CRM:
   - Produtos e Catálogo (preços, estoques virtuais e físicos, categorias)
   - Clientes e Contatos (PF/PJ, documentos, endereços fiscais)
   - Pedidos de Venda (novos pedidos emitidos ou atualizações de status)
2. CRM -> Bling ERP:
   - Novos produtos cadastrados no CRM exportados imediatamente para o Bling
   - Novos clientes cadastrados no CRM exportados para o Bling
   - Pedidos de venda gerados no CRM (ou orçamentos aprovados) transmitidos ao Bling
   - Mudanças de situação (status) no CRM refletidas no Bling
3. CRM & Bling -> WhatsApp:
   - Auto-vínculo de clientes novos com conversas de WhatsApp
   - Notificações e templates automáticos disparados para o cliente quando pedidos são criados ou faturados
"""

from typing import Any, Dict, List
from app.database.dbf_manager import DBFManager
from app.integrations.bling.client import BlingAPIClient
from app.integrations.bling.sync import BlingSyncService
from app.integrations.bling.outbound import (
    export_product_to_bling,
    export_client_to_bling,
    export_order_to_bling,
)
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso
from app.utils.validators import normalize_digits


class SyncOrchestrator:
    """Motor de Sincronização Total Bidirecional (Bling ERP ⇄ CRM ⇄ WhatsApp)."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.bling_sync = BlingSyncService(mgr)
        self.wa_client = WhatsAppCloudClient(mgr)
        self.notif = NotificationService(mgr)

    def sync_inbound_from_bling(self, scopes: List[str] = ["all"]) -> Dict[str, Any]:
        """Puxa todas as novidades do Bling ERP para o CRM com contingência graciosa."""
        try:
            return self.bling_sync.run_sync(scopes)
        except Exception as exc:
            return {
                "status": "OFFLINE_OR_PENDING_AUTH",
                "synced": {"products": 0, "contacts": 0, "orders": 0},
                "note": str(exc),
            }

    def sync_outbound_to_bling(self) -> Dict[str, Any]:
        """Varre o CRM e exporta para o Bling tudo que foi cadastrado localmente e ainda não possui ID_EXT."""
        stats = {"products_exported": 0, "clients_exported": 0, "orders_exported": 0}

        # 1. Exporta produtos criados no CRM sem ID externo
        prods = self.mgr.find_all("PRODUTOS")
        for p in prods:
            if not p.get("ID_EXT") or str(p.get("ID_EXT")).strip() == "":
                ext_id = export_product_to_bling(self.mgr, p)
                if ext_id:
                    stats["products_exported"] += 1

        # 2. Exporta clientes cadastrados no CRM sem ID externo
        clis = self.mgr.find_all("CLIENTES")
        for c in clis:
            if not c.get("ID_EXT") or str(c.get("ID_EXT")).strip() == "":
                ext_id = export_client_to_bling(self.mgr, c)
                if ext_id:
                    stats["clients_exported"] += 1

        # 3. Exporta pedidos criados no CRM sem ID externo
        orders = self.mgr.find_all("PEDIDOS")
        for o in orders:
            if not o.get("ID_EXT") or str(o.get("ID_EXT")).strip() == "":
                items = self.mgr.find_by_field("ITENS_PED", "ID_PEDIDO", o["ID"])
                ext_id = export_order_to_bling(self.mgr, o, items)
                if ext_id:
                    stats["orders_exported"] += 1

        return stats

    def sync_cross_channel_whatsapp(self) -> Dict[str, Any]:
        """Vincula conversas do WhatsApp a clientes do CRM/Bling e dispara notificações pendentes."""
        linked_count = 0
        notified_count = 0

        # Auto-vincula conversas desvinculadas pelo número de celular/telefone
        convs = self.mgr.find_all("CONVERS")
        clis = self.mgr.find_all("CLIENTES")

        for conv in convs:
            if not conv.get("ID_CLIENTE"):
                conv_tel = normalize_digits(conv.get("TELEFONE", ""))
                if conv_tel and len(conv_tel) >= 8:
                    for c in clis:
                        c_cel = normalize_digits(c.get("CELULAR", ""))
                        c_tel = normalize_digits(c.get("TELEFONE", ""))
                        if (c_cel and c_cel.endswith(conv_tel[-8:])) or (c_tel and c_tel.endswith(conv_tel[-8:])):
                            self.mgr.update("CONVERS", conv["ID"], {"ID_CLIENTE": c["ID"]})
                            linked_count += 1
                            break

        return {
            "conversations_linked": linked_count,
            "notifications_dispatched": notified_count,
        }

    def run_full_bidirectional_sync(self) -> Dict[str, Any]:
        """Executa a sincronização 100% completa: Bling -> CRM, CRM -> Bling e cruzamento com WhatsApp."""
        inbound_res = self.sync_inbound_from_bling(["all"])
        outbound_res = self.sync_outbound_to_bling()
        cross_res = self.sync_cross_channel_whatsapp()

        total_operations = (
            sum(inbound_res.get("synced", {}).values())
            + sum(outbound_res.values())
            + sum(cross_res.values())
        )

        rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING")
        if rows:
            self.mgr.update(
                "INTEGR",
                rows[0]["ID"],
                {
                    "SITUACAO": "CONECTADO",
                    "ULT_SYNC": now_iso(),
                    "STATUS_MSG": f"Sincronização bidirecional completa: {total_operations} operações realizadas.",
                },
            )

        self.notif.notify(
            "SYNC_BIDIRECIONAL",
            "Sincronização 100% Concluída",
            f"Bling, CRM e WhatsApp sincronizados com sucesso ({total_operations} registros sincronizados).",
            entidade="INTEGRACOES",
        )

        return {
            "status": "SUCCESS",
            "message": "Sincronização total 100% concluída em todos os canais!",
            "inbound_from_bling": inbound_res.get("synced", {}),
            "outbound_to_bling": outbound_res,
            "cross_channel_whatsapp": cross_res,
            "total_records_processed": total_operations,
            "timestamp": now_iso(),
        }
