import React, { useEffect, useState } from 'react';
import { ArrowRightCircle, CheckCircle, FileText, Plus, Trash2, X, XCircle } from 'lucide-react';
import { apiRequest } from '../services/api';
import {
  ClientRecord,
  OrderItemRecord,
  PaginatedResponse,
  ProductRecord,
  QuotationRecord,
} from '../types/crm';

export const QuotationsPage: React.FC = () => {
  const [quotations, setQuotations] = useState<QuotationRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [situacaoFilter, setSituacaoFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [clientId, setClientId] = useState('');
  const [dtValid, setDtValid] = useState('2026-12-01');
  const [frete, setFrete] = useState(0);
  const [obs, setObs] = useState('');
  const [items, setItems] = useState<Array<OrderItemRecord & { OBS_ITEM?: string }>>([]);

  const loadData = async () => {
    try {
      const params = new URLSearchParams();
      if (situacaoFilter) params.set('situacao', situacaoFilter);
      const [qRes, cRes, pRes] = await Promise.all([
        apiRequest<PaginatedResponse<QuotationRecord>>(`/quotations?${params.toString()}`),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=200'),
        apiRequest<PaginatedResponse<ProductRecord>>('/products?page_size=200'),
      ]);
      setQuotations(qRes.items);
      setClients(cRes.items);
      setProducts(pRes.items);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadData();
  }, [situacaoFilter]);

  const addItem = () => {
    if (products.length === 0) return;
    const first = products[0];
    setItems([
      ...items,
      {
        ID_PRODUTO: first.ID,
        QUANTIDADE: 100,
        PRECO_UNIT: first.PRECO,
        DESC_VALOR: 0,
        OBS_ITEM: '',
      },
    ]);
  };

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (items.length === 0) {
      setError('Inclua pelo menos 1 produto na proposta.');
      return;
    }
    try {
      await apiRequest('/quotations', {
        method: 'POST',
        body: JSON.stringify({
          ID_CLIENTE: clientId,
          DT_VALID: dtValid,
          FRETE: Number(frete || 0),
          OBS: obs,
          SITUACAO: 'ENVIADO',
          ITEMS: items,
        }),
      });
      setModalOpen(false);
      setItems([]);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleStatusChange = async (id: string, situacao: string) => {
    try {
      await apiRequest(`/quotations/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ SITUACAO: situacao }),
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleConvert = async (id: string) => {
    setError(null);
    try {
      const order = await apiRequest<{ NUMERO: string }>(`/quotations/${id}/convert-to-order`, {
        method: 'POST',
      });
      setFeedback(`Orçamento convertido com sucesso no pedido ${order.NUMERO}!`);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Módulo de Orçamentos e Propostas</h1>
          <p className="text-xs text-slate-500">
            Controle de validade, alçada de descontos, aprovação e conversão direta em pedido.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setModalOpen(true);
            if (items.length === 0 && products.length > 0) addItem();
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#053679] text-white text-xs font-semibold"
        >
          <Plus className="w-4 h-4" /> Novo Orçamento
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}
      {feedback && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-semibold">
          {feedback}
        </div>
      )}

      <div className="bg-slate-100/80 p-1.5 rounded-xl border border-slate-200/80 flex flex-wrap gap-1.5 shadow-2xs">
        {[
          '',
          'RASCUNHO',
          'EM_ELABORACAO',
          'ENVIADO',
          'EM_NEGOCIACAO',
          'APROVADO',
          'REPROVADO',
          'CONVERTIDO',
        ].map((st) => (
          <button
            key={st || 'ALL'}
            type="button"
            onClick={() => setSituacaoFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              situacaoFilter === st
                ? 'bg-[#053679] text-white shadow-sm'
                : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/60 hover:bg-white/90'
            }`}
          >
            {st || 'Todos'}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px] font-semibold">
              <th className="py-3 px-4">Número</th>
              <th className="py-3 px-4">Cliente</th>
              <th className="py-3 px-4">Validade</th>
              <th className="py-3 px-4">Desconto</th>
              <th className="py-3 px-4">Total</th>
              <th className="py-3 px-4">Situação</th>
              <th className="py-3 px-4 text-right">Ações Comerciais</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {quotations.map((q) => {
              const statusColor =
                q.SITUACAO === 'APROVADO' || q.SITUACAO === 'CONVERTIDO'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200/70'
                  : q.SITUACAO === 'ENVIADO' || q.SITUACAO === 'EM_NEGOCIACAO'
                  ? 'bg-blue-50 text-blue-700 border-blue-200/70'
                  : q.SITUACAO === 'REPROVADO'
                  ? 'bg-red-50 text-red-700 border-red-200/70'
                  : 'bg-amber-50 text-amber-700 border-amber-200/70';

              return (
                <tr key={q.ID} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-sky-800">{q.NUMERO}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{q.CLIENTE_NOME}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{q.DT_VALID}</td>
                  <td className="py-3 px-4 font-mono">
                    R$ {q.DESCONTO.toFixed(2)} ({q.DESC_PERC}%)
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">
                    R$ {q.TOTAL.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${statusColor}`}>
                      {q.SITUACAO}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                    {q.SITUACAO !== 'CONVERTIDO' && (
                      <>
                        <button
                          type="button"
                          onClick={() => void handleStatusChange(q.ID, 'APROVADO')}
                          title="Aprovar Orçamento"
                          className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200/80 text-emerald-700 hover:bg-emerald-100 transition-colors shadow-2xs"
                        >
                          <CheckCircle className="w-4 h-4 inline" />
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleStatusChange(q.ID, 'REPROVADO')}
                          title="Reprovar Orçamento"
                          className="p-1.5 rounded-lg bg-red-50 border border-red-200/80 text-red-600 hover:bg-red-100 transition-colors shadow-2xs"
                        >
                          <XCircle className="w-4 h-4 inline" />
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleConvert(q.ID)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold shadow-2xs transition-colors"
                        >
                          <ArrowRightCircle className="w-3.5 h-3.5" /> Converter em Pedido
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
            {quotations.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400">
                  Nenhum orçamento encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateQuotation}
            className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold flex items-center gap-2">
                <FileText className="w-5 h-5 text-sky-600" /> Elaborar Proposta Comercial
              </h2>
              <button type="button" onClick={() => setModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="font-semibold block mb-1">Cliente *</label>
                <select
                  required
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">Selecione o cliente...</option>
                  {clients.map((c) => (
                    <option key={c.ID} value={c.ID}>
                      {c.NOME}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Validade da Proposta *</label>
                <input
                  type="date"
                  required
                  value={dtValid}
                  onChange={(e) => setDtValid(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold">Produtos Orçados</span>
                <button
                  type="button"
                  onClick={addItem}
                  className="text-sky-700 font-semibold hover:underline"
                >
                  + Adicionar Item
                </button>
              </div>
              {items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 items-center bg-slate-50 p-2 rounded-lg">
                  <div className="col-span-5">
                    <select
                      value={item.ID_PRODUTO}
                      onChange={(e) => {
                        const prd = products.find((p) => p.ID === e.target.value);
                        const copy = [...items];
                        copy[idx] = {
                          ...copy[idx],
                          ID_PRODUTO: e.target.value,
                          PRECO_UNIT: prd ? prd.PRECO : 0,
                        };
                        setItems(copy);
                      }}
                      className="w-full px-2 py-1.5 border border-slate-300 rounded bg-white"
                    >
                      {products.map((p) => (
                        <option key={p.ID} value={p.ID}>
                          {p.CODIGO} — {p.NOME}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      min="1"
                      value={item.QUANTIDADE}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].QUANTIDADE = Number(e.target.value);
                        setItems(copy);
                      }}
                      className="w-full px-2 py-1.5 border border-slate-300 rounded bg-white font-mono"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      value={item.PRECO_UNIT}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].PRECO_UNIT = Number(e.target.value);
                        setItems(copy);
                      }}
                      className="w-full px-2 py-1.5 border border-slate-300 rounded bg-white font-mono"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      value={item.DESC_VALOR}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].DESC_VALOR = Number(e.target.value);
                        setItems(copy);
                      }}
                      placeholder="Desc R$"
                      className="w-full px-2 py-1.5 border border-slate-300 rounded bg-white font-mono"
                    />
                  </div>
                  <div className="col-span-1 text-right">
                    <button
                      type="button"
                      onClick={() => setItems(items.filter((_, i) => i !== idx))}
                      className="text-red-600"
                    >
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div>
              <label className="font-semibold block mb-1">Observações e Condições de Entrega</label>
              <textarea
                rows={2}
                value={obs}
                onChange={(e) => setObs(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-lg bg-[#053679] text-white font-semibold"
              >
                Salvar Orçamento
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};


