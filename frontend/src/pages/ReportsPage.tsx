import React, { useEffect, useState } from 'react';
import { BarChart3, Download, Filter } from 'lucide-react';
import { apiRequest, downloadAuthorizedCsv } from '../services/api';

const REPORT_TYPES = [
  { id: 'sales', label: '1. Vendas por Período' },
  { id: 'revenue', label: '2. Faturamento Comercial' },
  { id: 'orders', label: '3. Pedidos por Situação' },
  { id: 'clients', label: '4. Clientes Cadastrados e Origem' },
  { id: 'products', label: '5. Catálogo de Produtos e Estoque' },
  { id: 'quotations', label: '6. Orçamentos Emitidos e Conversão' },
  { id: 'opportunities', label: '7. Oportunidades no Funil' },
  { id: 'conversion', label: '8. Taxa de Conversão Comercial' },
  { id: 'activities', label: '9. Atividades e Cumprimento de Prazo' },
  { id: 'performance', label: '10. Desempenho Comercial por Responsável' },
];

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState('sales');
  const [situacao, setSituacao] = useState('');
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const loadReport = async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (situacao) q.set('situacao', situacao);
      const res = await apiRequest<{
        report_type: string;
        count: number;
        rows: Array<Record<string, unknown>>;
      }>(`/reports/${reportType}?${q.toString()}`);
      setRows(res.rows);
      setCount(res.count);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [reportType, situacao]);

  const columns = rows.length > 0 ? Object.keys(rows[0]).slice(0, 8) : [];

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Relatórios Comerciais e Exportação</h1>
          <p className="text-sm text-slate-500">
            Extração analítica em tempo real diretamente das tabelas DBF com exportação CSV.
          </p>
        </div>
        <button
          onClick={() =>
            downloadAuthorizedCsv(
              `/reports/${reportType}/csv${situacao ? `?situacao=${situacao}` : ''}`,
              `relatorio_${reportType}.csv`
            )
          }
          className="satiro-btn-primary"
        >
          <Download className="w-4 h-4" /> Exportar Relatório CSV
        </button>
      </div>

      <div className="satiro-card p-4 flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-bold uppercase text-slate-500">Tipo de Relatório:</span>
          </div>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="satiro-input min-w-[280px]"
          >
            {REPORT_TYPES.map((rt) => (
              <option key={rt.id} value={rt.id}>
                {rt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <input
            value={situacao}
            onChange={(e) => setSituacao(e.target.value)}
            placeholder="Filtrar por situação (ex: ATIVO, GANHA)..."
            className="satiro-input text-xs min-w-[240px]"
          />
          <span className="satiro-badge bg-blue-50 text-blue-700 shrink-0">
            {count} registro(s)
          </span>
        </div>
      </div>

      <div className="satiro-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase">
                {columns.length > 0 ? (
                  columns.map((col) => (
                    <th key={col} className="py-3 px-4">
                      {col}
                    </th>
                  ))
                ) : (
                  <th className="py-3 px-4">Resultado</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    Processando relatório...
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    Nenhum registro encontrado para os filtros informados.
                  </td>
                </tr>
              ) : (
                rows.slice(0, 50).map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    {columns.map((col) => (
                      <td key={col} className="py-2.5 px-4 text-slate-700 font-mono">
                        {String(row[col] ?? '-')}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

