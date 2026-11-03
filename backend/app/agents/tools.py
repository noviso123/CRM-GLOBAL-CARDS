from typing import Any, Dict, List
from app.agents.crm_context import CRMContextBuilder


def get_authorized_tools_manifest() -> List[Dict[str, Any]]:
    """Lista de ferramentas controladas compatíveis com padrão MCP / Tool Calling."""
    return [
        {
            "name": "query_crm_indicators",
            "description": "Consulta indicadores reais de vendas, clientes, pedidos e funil comercial.",
            "requires_confirmation": False,
        },
        {
            "name": "search_catalog_products",
            "description": "Consulta catálogo de produtos, preços e saldos de estoque.",
            "requires_confirmation": False,
        },
        {
            "name": "summarize_client_relationship",
            "description": "Resume o histórico completo de relacionamento de um cliente.",
            "requires_confirmation": False,
        },
        {
            "name": "propose_follow_up_activity",
            "description": "Prepara proposta de agendamento de atividade comercial (requer aprovação humana para gravar).",
            "requires_confirmation": True,
        },
        {
            "name": "draft_whatsapp_reply",
            "description": "Prepara rascunho de resposta comercial para WhatsApp (requer autorização humana para envio).",
            "requires_confirmation": True,
        },
    ]


def execute_read_tool(ctx: CRMContextBuilder, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    snap = ctx.build_snapshot()
    if tool_name == "query_crm_indicators":
        return {"kpis": snap["kpis"]}
    if tool_name == "search_catalog_products":
        q = str(args.get("query", "")).strip()
        prods = ctx.product_svc.list_products(search=q)
        return {"products": prods[:10]}
    if tool_name == "summarize_client_relationship":
        cid = str(args.get("client_id", "")).strip()
        if cid:
            return ctx.client_svc.get_client_overview_10_tabs(cid)
    return snap

