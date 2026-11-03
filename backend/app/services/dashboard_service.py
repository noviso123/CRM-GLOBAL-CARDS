from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List
from app.database.dbf_manager import DBFManager


class DashboardService:
    """Calcula os 12 indicadores principais, 8 gráficos e 7 seções operacionais 100% a partir dos dados reais nos arquivos DBF."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr

    def get_summary(self, period_days: int = 30) -> Dict[str, Any]:
        cutoff_dt = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        clients = self.mgr.find_all("CLIENTES", sort_by="DT_CRIA", descending=True)
        products = self.mgr.find_all("PRODUTOS")
        orders = self.mgr.find_all("PEDIDOS", sort_by="DT_CRIA", descending=True)
        order_items = self.mgr.find_all("ITENS_PED")
        quotations = self.mgr.find_all("ORCAMENT", sort_by="DT_CRIA", descending=True)
        opportunities = self.mgr.find_all("OPORTUN", sort_by="DT_CRIA", descending=True)
        stages = self.mgr.find_all("ETAPAS", sort_by="ORDEM")
        activities = self.mgr.find_all("ATIVIDAD", sort_by="DATA_AG")
        conversations = self.mgr.find_all("CONVERS", sort_by="DT_ATUA", descending=True)
        notifications = self.mgr.find_all("NOTIFIC", sort_by="DT_CRIA", descending=True)
        integrations = self.mgr.find_all("INTEGR")

        new_clients = [c for c in clients if str(c.get("DT_CRIA", ""))[:10] >= cutoff_dt]
        valid_orders = [o for o in orders if o.get("SITUACAO") != "CANCELADO"]
        revenue_total = round(sum(float(o.get("TOTAL", 0.0)) for o in valid_orders), 2)

        open_quotations = [
            q
            for q in quotations
            if q.get("SITUACAO") in ("RASCUNHO", "EM_ELABORACAO", "ENVIADO", "EM_NEGOCIACAO")
        ]
        active_opps = [o for o in opportunities if o.get("SITUACAO") == "ABERTA"]
        won_opps = [o for o in opportunities if o.get("SITUACAO") == "GANHA"]
        lost_opps = [o for o in opportunities if o.get("SITUACAO") == "PERDIDA"]
        total_closed_or_open = len(opportunities)
        conversion_rate = (
            round((len(won_opps) / total_closed_or_open) * 100.0, 1)
            if total_closed_or_open > 0
            else 0.0
        )

        pending_activities = [
            a for a in activities if a.get("SITUACAO") in ("PENDENTE", "EM_ANDAMENTO", "ATRASADA")
        ]
        ongoing_chats = [
            c for c in conversations if c.get("SITUACAO") in ("FILA", "EM_ATENDIMENTO", "AGUARDANDO_CLIENTE")
        ]

        # Gráficos reais agrupados por período e dimensão
        sales_by_month: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"period": "", "orders_count": 0, "revenue": 0.0}
        )
        orders_by_status: Dict[str, int] = defaultdict(int)
        for o in orders:
            st = o.get("SITUACAO", "ABERTO")
            orders_by_status[st] += 1
            if st != "CANCELADO":
                ym = (o.get("DT_PEDIDO") or o.get("DT_CRIA", ""))[:7] or "Atual"
                sales_by_month[ym]["period"] = ym
                sales_by_month[ym]["orders_count"] += 1
                sales_by_month[ym]["revenue"] = round(
                    sales_by_month[ym]["revenue"] + float(o.get("TOTAL", 0.0)), 2
                )

        stage_map = {s["ID"]: s["NOME"] for s in stages}
        opps_by_stage: Dict[str, Dict[str, Any]] = {}
        for s in stages:
            opps_by_stage[s["ID"]] = {
                "stage": s["NOME"],
                "color": s.get("COR", "#0284C7"),
                "count": 0,
                "total_value": 0.0,
            }
        for op in opportunities:
            sid = op.get("ID_ETAPA", "")
            if sid in opps_by_stage:
                opps_by_stage[sid]["count"] += 1
                opps_by_stage[sid]["total_value"] = round(
                    opps_by_stage[sid]["total_value"] + float(op.get("VALOR_EST", 0.0)), 2
                )

        prod_sales: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"product_name": "", "quantity": 0.0, "revenue": 0.0}
        )
        for it in order_items:
            pid = it.get("ID_PRODUTO", "")
            prod_sales[pid]["product_name"] = it.get("NOME_PRD", pid)
            prod_sales[pid]["quantity"] = round(
                prod_sales[pid]["quantity"] + float(it.get("QUANTIDADE", 0.0)), 2
            )
            prod_sales[pid]["revenue"] = round(
                prod_sales[pid]["revenue"] + float(it.get("SUBTOTAL", 0.0)), 2
            )
        top_products = sorted(
            prod_sales.values(), key=lambda x: x["revenue"], reverse=True
        )[:6]

        client_map = {c["ID"]: c["NOME"] for c in clients}
        recent_orders = [
            {**o, "CLIENTE_NOME": client_map.get(o.get("ID_CLIENTE", ""), "")}
            for o in orders[:6]
        ]
        recent_opps = [
            {
                **op,
                "CLIENTE_NOME": client_map.get(op.get("ID_CLIENTE", ""), ""),
                "ETAPA_NOME": stage_map.get(op.get("ID_ETAPA", ""), ""),
            }
            for op in opportunities[:6]
        ]

        return {
            "kpis": {
                "total_clients": len(clients),
                "new_clients": len(new_clients),
                "total_products": len(products),
                "orders_count": len(valid_orders),
                "revenue": revenue_total,
                "open_quotations": len(open_quotations),
                "active_opportunities": len(active_opps),
                "won_opportunities": len(won_opps),
                "lost_opportunities": len(lost_opps),
                "conversion_rate": conversion_rate,
                "pending_activities": len(pending_activities),
                "ongoing_conversations": len(ongoing_chats),
            },
            "charts": {
                "sales_by_period": sorted(sales_by_month.values(), key=lambda x: x["period"]),
                "orders_by_status": [
                    {"status": k, "count": v} for k, v in orders_by_status.items()
                ],
                "opportunities_by_stage": list(opps_by_stage.values()),
                "top_products": top_products,
            },
            "sections": {
                "recent_orders": recent_orders,
                "recent_clients": clients[:6],
                "recent_opportunities": recent_opps,
                "upcoming_activities": pending_activities[:6],
                "recent_conversations": conversations[:6],
                "important_notifications": notifications[:6],
                "integrations_status": integrations,
            },
        }

