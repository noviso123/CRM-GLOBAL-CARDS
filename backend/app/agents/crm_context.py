from typing import Any, Dict
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.services.activity_service import ActivityService
from app.services.client_service import ClientService
from app.services.dashboard_service import DashboardService
from app.services.opportunity_service import OpportunityService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.quotation_service import QuotationService


class CRMContextBuilder:
    """Constrói contexto comercial somente através dos serviços de domínio e respeitando as permissões do usuário."""

    def __init__(self, mgr: DBFManager, current_user: Dict[str, Any]):
        self.mgr = mgr
        self.user = current_user
        self.dashboard_svc = DashboardService(mgr)
        self.client_svc = ClientService(mgr)
        self.product_svc = ProductService(mgr)
        self.order_svc = OrderService(mgr)
        self.quote_svc = QuotationService(mgr)
        self.opp_svc = OpportunityService(mgr)
        self.act_svc = ActivityService(mgr)

    def build_snapshot(self) -> Dict[str, Any]:
        check_permission(self.mgr, self.user, "IA", "view")
        summary = self.dashboard_svc.get_summary()
        clients = self.client_svc.list_clients()[:10]
        products = self.product_svc.list_products()[:15]
        opps = self.opp_svc.list_opportunities()[:10]
        activities = self.act_svc.list_activities(situacao="PENDENTE")[:10]
        return {
            "kpis": summary["kpis"],
            "clients": [
                {"id": c["ID"], "codigo": c["CODIGO"], "nome": c["NOME"], "situacao": c["SITUACAO"]}
                for c in clients
            ],
            "products": [
                {
                    "id": p["ID"],
                    "codigo": p["CODIGO"],
                    "nome": p["NOME"],
                    "preco": p["PRECO"],
                    "estoque": p["ESTOQUE"],
                }
                for p in products
            ],
            "opportunities": [
                {
                    "id": o["ID"],
                    "titulo": o["TITULO"],
                    "cliente": o.get("CLIENTE_NOME", ""),
                    "etapa": o.get("ETAPA_NOME", ""),
                    "valor": o["VALOR_EST"],
                    "probabilidade": o["PROBABIL"],
                }
                for o in opps
            ],
            "pending_activities": [
                {"id": a["ID"], "titulo": a["TITULO"], "data": a["DATA_AG"], "prioridade": a["PRIORIDADE"]}
                for a in activities
            ],
        }

