import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Award,
  Briefcase,
  CheckCircle2,
  DollarSign,
  FileText,
  MessageSquare,
  Package,
  RefreshCw,
  ShoppingCart,
  TrendingUp,
  UserPlus,
  Users,
  XCircle,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import { DashboardSummary } from '../types/crm';

export const DashboardPage: React.FC = () => {
  const [period, setPeriod] = useState<number>(30);
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async (days: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<DashboardSummary>(`/dashboard/summary?period_days=${days}`);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar indicadores.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSummary(period);
  }, [period]);

  if (loading && !data) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        Calculando indicadores reais a partir dos arquivos DBF...
      </div>
    );
  }

  const k = data?.kpis;

  const kpiCards = [
    {
      label: 'Total de Clientes',
      value: k?.total_clients ?? 0,
      sub: `${k?.new_clients ?? 0} novos no período`,
      icon: Users,
      color: 'bg-sky-50 text-sky-700 border-sky-200',
    },
    {
      label: 'Novos Clientes',
      value: k?.new_clients ?? 0,
      sub: `Últimos ${period} dias`,
      icon: UserPlus,
      color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    },
    {
      label: 'Total de Produtos',
      value: k?.total_products ?? 0,
      sub: 'Catálogo ativo',
      icon: Package,
      color: 'bg-slate-100 text-slate-700 border-slate-200',
    },
    {
      label: 'Pedidos Realizados',
      value: k?.orders_count ?? 0,
      sub: 'Pedidos válidos',
      icon: ShoppingCart,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
      label: 'Faturamento Acumulado',
      value: `R$ ${(k?.revenue ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      sub: 'Soma real dos pedidos',
      icon: DollarSign,
      color: 'bg-emerald-100/80 text-emerald-800 border-emerald-300',
    },
    {
      label: 'Orçamentos em Aberto',
      value: k?.open_quotations ?? 0,
      sub: 'Propostas ativas',
      icon: FileText,
      color: 'bg-amber-50 text-amber-700 border-amber-200',
    },
    {
      label: 'Oportunidades Ativas',
      value: k?.active_opportunities ?? 0,
      sub: 'No funil comercial',
      icon: Briefcase,
      color: 'bg-blue-50 text-blue-700 border-blue-200',
    },
    {
      label: 'Oportunidades Ganhas',
      value: k?.won_opportunities ?? 0,
      sub: 'Negócios fechados',
      icon: Award,
      color: 'bg-green-50 text-green-700 border-green-200',
    },
    {
      label: 'Oportunidades Perdidas',
      value: k?.lost_opportunities ?? 0,
      sub: 'Com registro de motivo',
      icon: XCircle,
      color: 'bg-red-50 text-red-700 border-red-200',
    },
    {
      label: 'Taxa de Conversão',
      value: `${k?.conversion_rate ?? 0}%`,
      sub: 'Ganhas / Total funil',
      icon: TrendingUp,
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      label: 'Atividades Pendentes',
      value: k?.pending_activities ?? 0,
      sub: 'Acompanhamento comercial',
      icon: Activity,
      color: 'bg-orange-50 text-orange-700 border-orange-200',
    },
    {
      label: 'Atendimentos WhatsApp',
      value: k?.ongoing_conversations ?? 0,
      sub: 'Conversas em andamento',
      icon: MessageSquare,
      color: 'bg-teal-50 text-teal-700 border-teal-200',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard Gerencial</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Indicadores calculados em tempo real a partir dos 21 arquivos DBF locais.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90, 365].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setPeriod(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                period === d
                  ? 'bg-[#0F3D6E] text-white border-[#0F3D6E]'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {d} dias
            </button>
          ))}
          <button
            type="button"
            onClick={() => void loadSummary(period)}
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100"
            title="Atualizar dados"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* 12 Indicadores Principais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-start justify-between"
            >
              <div>
                <span className="text-xs font-medium text-slate-500">{card.label}</span>
                <p className="text-xl font-bold text-slate-900 mt-1 tabular-nums">{card.value}</p>
                <span className="text-[11px] text-slate-400 block mt-1">{card.sub}</span>
              </div>
              <div className={`p-2.5 rounded-xl border ${card.color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Gráficos Comerciais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Oportunidades por Etapa do Funil */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Oportunidades por Etapa do Funil</h2>
              <p className="text-xs text-slate-500">Distribuição financeira e volume por coluna</p>
            </div>
            <Link to="/funil" className="text-xs font-semibold text-sky-600 hover:underline">
              Abrir Kanban →
            </Link>
          </div>
          <div className="space-y-3">
            {(data?.charts.opportunities_by_stage || []).map((st) => {
              const maxCount = Math.max(
                1,
                ...(data?.charts.opportunities_by_stage.map((x) => x.count) || [1])
              );
              const pct = Math.round((st.count / maxCount) * 100);
              return (
                <div key={st.stage} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{st.stage}</span>
                    <span className="font-mono text-slate-600 tabular-nums">
                      {st.count} oport. • R${' '}
                      {st.total_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${Math.max(pct, st.count > 0 ? 8 : 0)}%`, backgroundColor: st.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Produtos Mais Vendidos & Desempenho por Período */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Produtos Mais Vendidos & Faturamento por Período
                </h2>
                <p className="text-xs text-slate-500">Ranking real por receita gerada nos pedidos</p>
              </div>
              <Link to="/produtos" className="text-xs font-semibold text-sky-600 hover:underline">
                Ver Catálogo →
              </Link>
            </div>
            {(data?.charts.top_products || []).length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">
                Nenhum item faturado ainda. Crie um pedido ou converta um orçamento para visualizar o ranking.
              </p>
            ) : (
              <div className="space-y-2.5">
                {data?.charts.top_products.map((p) => (
                  <div
                    key={p.product_name}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 text-xs"
                  >
                    <span className="font-medium text-slate-800 truncate pr-3">
                      {p.product_name}
                    </span>
                    <span className="font-mono text-slate-700 shrink-0 tabular-nums">
                      {p.quantity} un • R${' '}
                      {p.revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase text-slate-500 mb-2">
              Pedidos por Situação
            </h3>
            <div className="flex flex-wrap gap-2">
              {(data?.charts.orders_by_status || []).map((st) => (
                <span
                  key={st.status}
                  className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold"
                >
                  {st.status}: {st.count}
                </span>
              ))}
              {(data?.charts.orders_by_status || []).length === 0 && (
                <span className="text-xs text-slate-400">Sem pedidos registrados.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Seções Operacionais Adicionais */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Últimos Pedidos */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900">Últimos Pedidos</h3>
            <Link to="/pedidos" className="text-xs text-sky-600 hover:underline">
              Ver todos
            </Link>
          </div>
          <div className="space-y-2">
            {(data?.sections.recent_orders || []).map((o) => (
              <div
                key={o.ID}
                className="p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-mono font-bold text-slate-900">{o.NUMERO}</span>
                  <p className="text-slate-500 truncate max-w-[160px]">{o.CLIENTE_NOME}</p>
                </div>
                <div className="text-right">
                  <span className="font-mono font-bold text-emerald-700 block">
                    R$ {o.TOTAL.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {o.SITUACAO}
                  </span>
                </div>
              </div>
            ))}
            {(data?.sections.recent_orders || []).length === 0 && (
              <p className="text-xs text-slate-400 py-4 text-center">Nenhum pedido registrado.</p>
            )}
          </div>
        </div>

        {/* Últimos Clientes & Oportunidades */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900">Últimos Clientes Cadastrados</h3>
            <Link to="/clientes" className="text-xs text-sky-600 hover:underline">
              Ver todos
            </Link>
          </div>
          <div className="space-y-2">
            {(data?.sections.recent_clients || []).map((c) => (
              <div
                key={c.ID}
                className="p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 flex items-center justify-between text-xs"
              >
                <div>
                  <p className="font-semibold text-slate-800">{c.NOME}</p>
                  <span className="text-slate-400 font-mono text-[11px]">
                    {c.CODIGO} • {c.CIDADE || 'Local'} {c.UF}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700">
                  {c.ORIGEM}
                </span>
              </div>
            ))}
            {(data?.sections.recent_clients || []).length === 0 && (
              <p className="text-xs text-slate-400 py-4 text-center">Nenhum cliente cadastrado.</p>
            )}
          </div>
        </div>

        {/* Atividades Próximas e Situação das Integrações */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-slate-900">Atividades Pendentes</h3>
              <Link to="/atividades" className="text-xs text-sky-600 hover:underline">
                Agenda
              </Link>
            </div>
            <div className="space-y-2">
              {(data?.sections.upcoming_activities || []).map((a) => (
                <div
                  key={a.ID}
                  className="p-2.5 rounded-lg border border-slate-100 flex items-center justify-between text-xs"
                >
                  <div>
                    <p className="font-semibold text-slate-800">{a.TITULO}</p>
                    <span className="text-[11px] text-slate-500">
                      {a.TIPO} • {a.DATA_AG} às {a.HORA_AG}
                    </span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 text-[10px] font-bold">
                    {a.PRIORIDADE}
                  </span>
                </div>
              ))}
              {(data?.sections.upcoming_activities || []).length === 0 && (
                <p className="text-xs text-slate-400 py-2 text-center">
                  Nenhuma atividade pendente.
                </p>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100">
            <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">
              Situação das Integrações
            </h4>
            <div className="space-y-1.5">
              {(data?.sections.integrations_status || []).map((ig) => (
                <div
                  key={ig.ID}
                  className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-50"
                >
                  <span className="font-semibold text-slate-700">{ig.PROVEDOR}</span>
                  <span
                    className={`inline-flex items-center gap-1 font-medium ${
                      ig.SITUACAO === 'CONECTADO' ? 'text-emerald-700' : 'text-slate-500'
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> {ig.SITUACAO}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

