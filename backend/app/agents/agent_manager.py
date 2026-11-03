from typing import Any, Dict, Optional
from app.agents.crm_context import CRMContextBuilder
from app.agents.tools import get_authorized_tools_manifest
from app.database.dbf_manager import DBFManager


class AgentManager:
    """Orquestrador de IA comercial que opera estritamente sobre os serviços autorizados do CRM."""

    def __init__(self, mgr: DBFManager, current_user: Dict[str, Any]):
        self.mgr = mgr
        self.user = current_user
        self.ctx_builder = CRMContextBuilder(mgr, current_user)

    def process_prompt(
        self, prompt: str, client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        snap = self.ctx_builder.build_snapshot()
        kpis = snap["kpis"]
        products = snap["products"]
        opps = snap["opportunities"]

        prod_lines = (
            ", ".join(f"{p['nome']} ({p['codigo']}: R$ {p['preco']:.2f}, Est: {p['estoque']})" for p in products[:5])
            if products
            else "Nenhum produto cadastrado ainda."
        )
        opp_lines = (
            "; ".join(f"{o['titulo']} - {o['cliente']} (Etapa: {o['etapa']}, R$ {o['valor']:.2f})" for o in opps[:5])
            if opps
            else "Nenhuma oportunidade ativa no momento."
        )

        client_summary = ""
        if client_id:
            ov = self.ctx_builder.client_svc.get_client_overview_10_tabs(client_id)
            cli = ov["client"]
            client_summary = (
                f"\n\n### Contexto do Cliente Selecionado: {cli['NOME']} ({cli['CODIGO']})\n"
                f"- Pedidos realizados: {len(ov['orders'])}\n"
                f"- Orçamentos: {len(ov['quotations'])}\n"
                f"- Oportunidades: {len(ov['opportunities'])}\n"
                f"- Última interação: {cli.get('DT_ULT_INT', 'N/A')}"
            )

        answer = (
            f"### Análise Comercial CRM GLOBAL CARDS\n"
            f"Com base nos dados reais armazenados localmente:\n"
            f"- **Clientes Ativos:** {kpis['total_clients']} ({kpis['new_clients']} novos no período)\n"
            f"- **Pedidos Realizados:** {kpis['orders_count']} | **Faturamento Acumulado:** R$ {kpis['revenue']:.2f}\n"
            f"- **Orçamentos em Aberto:** {kpis['open_quotations']}\n"
            f"- **Funil Comercial:** {kpis['active_opportunities']} oportunidades ativas, "
            f"{kpis['won_opportunities']} ganhas (Taxa de conversão: {kpis['conversion_rate']}%)\n"
            f"- **Atividades Pendentes:** {kpis['pending_activities']}\n\n"
            f"**Catálogo em Destaque:** {prod_lines}\n\n"
            f"**Pipeline Atual:** {opp_lines}"
            f"{client_summary}\n\n"
            f"**Sugestão de Ação Comercial:** Priorize o acompanhamento dos {kpis['open_quotations']} orçamento(s) em aberto "
            f"e das {kpis['pending_activities']} atividade(s) pendente(s). Qualquer alteração de registro ou envio de mensagem exige sua confirmação explícita."
        )

        return {
            "prompt": prompt,
            "answer": answer,
            "context_summary": kpis,
            "available_tools": get_authorized_tools_manifest(),
            "requires_human_approval_for_writes": True,
        }

