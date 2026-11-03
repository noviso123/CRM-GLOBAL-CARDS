from typing import Any, Dict
from app.core.exceptions import IntegrityErrorCRM, NotFoundErrorCRM
from app.database.dbf_manager import DBFManager


class IntegrityValidator:
    """Garante integridade referencial entre os 21 arquivos DBF no backend Python."""

    def __init__(self, manager: DBFManager):
        self.mgr = manager

    def require_client(self, client_id: str) -> Dict[str, Any]:
        cli = self.mgr.get_by_id("CLIENTES", client_id)
        if not cli:
            raise IntegrityErrorCRM(
                f"Cliente referenciado ('{client_id}') não existe em CLIENTES.DBF.",
                details={"entity": "CLIENTES", "id": client_id},
            )
        return cli

    def require_product(self, product_id: str) -> Dict[str, Any]:
        prd = self.mgr.get_by_id("PRODUTOS", product_id)
        if not prd:
            raise IntegrityErrorCRM(
                f"Produto referenciado ('{product_id}') não existe em PRODUTOS.DBF.",
                details={"entity": "PRODUTOS", "id": product_id},
            )
        return prd

    def require_order(self, order_id: str) -> Dict[str, Any]:
        ped = self.mgr.get_by_id("PEDIDOS", order_id)
        if not ped:
            raise IntegrityErrorCRM(
                f"Pedido referenciado ('{order_id}') não existe em PEDIDOS.DBF.",
                details={"entity": "PEDIDOS", "id": order_id},
            )
        return ped

    def require_quotation(self, quotation_id: str) -> Dict[str, Any]:
        orc = self.mgr.get_by_id("ORCAMENT", quotation_id)
        if not orc:
            raise IntegrityErrorCRM(
                f"Orçamento referenciado ('{quotation_id}') não existe em ORCAMENT.DBF.",
                details={"entity": "ORCAMENT", "id": quotation_id},
            )
        return orc

    def validate_contact_insert(self, payload: Dict[str, Any]) -> None:
        client_id = str(payload.get("ID_CLIENTE", "")).strip()
        if not client_id:
            raise IntegrityErrorCRM("Todo contato deve estar associado a um cliente válido.")
        self.require_client(client_id)

    def validate_order_insert(self, payload: Dict[str, Any]) -> None:
        client_id = str(payload.get("ID_CLIENTE", "")).strip()
        if not client_id:
            raise IntegrityErrorCRM("Todo pedido deve possuir um cliente válido.")
        self.require_client(client_id)

    def validate_opportunity_insert(self, payload: Dict[str, Any]) -> None:
        client_id = str(payload.get("ID_CLIENTE", "")).strip()
        if not client_id:
            raise IntegrityErrorCRM("Toda oportunidade deve estar associada a um cliente válido.")
        self.require_client(client_id)
        stage_id = str(payload.get("ID_ETAPA", "")).strip()
        if stage_id and not self.mgr.get_by_id("ETAPAS", stage_id):
            raise IntegrityErrorCRM(f"Etapa de funil '{stage_id}' inexistente.")

    def check_client_can_be_deleted(self, client_id: str) -> None:
        if not self.mgr.get_by_id("CLIENTES", client_id):
            raise NotFoundErrorCRM("CLIENTES", client_id)
        orders = self.mgr.find_by_field("PEDIDOS", "ID_CLIENTE", client_id)
        if orders:
            raise IntegrityErrorCRM(
                f"Não é permitido excluir o cliente pois possui {len(orders)} pedido(s) registrado(s). Utilize a inativação.",
                details={"entity": "CLIENTES", "dependent": "PEDIDOS", "count": len(orders)},
            )
        quotations = self.mgr.find_by_field("ORCAMENT", "ID_CLIENTE", client_id)
        if quotations:
            raise IntegrityErrorCRM(
                f"Não é permitido excluir o cliente pois possui {len(quotations)} orçamento(s) vinculado(s).",
                details={"entity": "CLIENTES", "dependent": "ORCAMENT", "count": len(quotations)},
            )
        opportunities = self.mgr.find_by_field("OPORTUN", "ID_CLIENTE", client_id)
        if opportunities:
            raise IntegrityErrorCRM(
                f"Não é permitido excluir o cliente pois possui {len(opportunities)} oportunidade(s) vinculada(s).",
                details={"entity": "CLIENTES", "dependent": "OPORTUN", "count": len(opportunities)},
            )

    def check_product_can_be_deleted(self, product_id: str) -> None:
        if not self.mgr.get_by_id("PRODUTOS", product_id):
            raise NotFoundErrorCRM("PRODUTOS", product_id)
        order_items = self.mgr.find_by_field("ITENS_PED", "ID_PRODUTO", product_id)
        if order_items:
            raise IntegrityErrorCRM(
                f"Não é permitido excluir o produto pois está vinculado a {len(order_items)} item(ns) de pedido.",
                details={"entity": "PRODUTOS", "dependent": "ITENS_PED", "count": len(order_items)},
            )
        quote_items = self.mgr.find_by_field("ITENS_ORC", "ID_PRODUTO", product_id)
        if quote_items:
            raise IntegrityErrorCRM(
                f"Não é permitido excluir o produto pois está vinculado a {len(quote_items)} item(ns) de orçamento.",
                details={"entity": "PRODUTOS", "dependent": "ITENS_ORC", "count": len(quote_items)},
            )

