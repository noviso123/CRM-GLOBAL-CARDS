import React, { useEffect, useState } from 'react';
import { Eye, Plus, Search, ShoppingCart, Trash2, X } from 'lucide-react';
import { apiRequest } from '../services/api';
import {
  ClientRecord,
  OrderItemRecord,
  OrderRecord,
  PaginatedResponse,
  ProductRecord,
} from '../types/crm';

export const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [search, setSearch] = useState('');
  const [situacaoFilter, setSituacaoFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailOrder, setDetailOrder] = useState<OrderRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [clientId, setClientId] = useState('');
  const [condPagto, setCondPagto] = useState('28 dias no Boleto');
  const [frete, setFrete] = useState(0);
  const [obs, setObs] = useState('');
  const [items, setItems] = useState<OrderItemRecord[]>([]);

  const loadData = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (situacaoFilter) params.set('situacao', situacaoFilter);
      const [oRes, cRes, pRes] = await Promise.all([
        apiRequest<PaginatedResponse<OrderRecord>>(`/orders?${params.toString()}`),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=200'),
        apiRequest<PaginatedResponse<ProductRecord>>('/products?page_size=200'),
      ]);
      setOrders(oRes.items);
      setClients(cRes.items);
      setProducts(pRes.items);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadData();
  }, [search, situacaoFilter]);

  const addItemRow = () => {
    if (products.length === 0) return;
    const first = products[0];
    setItems([
      ...items,
      {
        ID_PRODUTO: first.ID,
        QUANTIDADE: 1,
        PRECO_UNIT: first.PRECO,
        DESC_VALOR: 0,
      },
    ]);
  };

  const subtotal = items.reduce((acc, it) => acc + it.QUANTIDADE * it.PRECO_UNIT, 0);
  const totalDiscount = items.reduce((acc, it) => acc + (it.DESC_VALOR || 0), 0);
  const finalTotal = Math.max(0, subtotal - totalDiscount + Number(frete || 0));

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (items.length === 0) {
      setError('Adicione pelo menos 1 produto ao pedido.');
      return;
    }
    try {
      await apiRequest('/orders', {
        method: 'POST',
        body: JSON.stringify({
          ID_CLIENTE: clientId,
          COND_PAGTO: condPagto,
          FRETE: Number(frete || 0),
          OBS: obs,
          ITEMS: items,
        }),
      });
      setModalOpen(false);
      setItems([]);
      setObs('');
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleStatusChange = async (orderId: string, newStatus: string) => {
    try {
      const updated = await apiRequest<OrderRecord>(`/orders/${orderId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ SITUACAO: newStatus }),
      });
      setDetailOrder(updated);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Pedidos e Vendas</h1>
          <p className="text-xs text-slate-500">
            Acompanhamento comercial, cálculo de descontos autorizados e rastreabilidade Bling.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setModalOpen(true);
            if (items.length === 0 && products.length > 0) addItemRow();
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0F3D6E] hover:bg-[#0B2D52] text-white text-xs font-semibold shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" /> Novo Pedido
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar por número do pedido, nome do cliente ou ID Bling..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-sky-600"
          />
        </div>
        <select
          value={situacaoFilter}
          onChange={(e) => setSituacaoFilter(e.target.value)}
          className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white"
        >
          <option value="">Todas as situações</option>
          <option value="ABERTO">ABERTO</option>
          <option value="APROVADO">APROVADO</option>
          <option value="FATURADO">FATURADO</option>
          <option value="ENTREGUE">ENTREGUE</option>
          <option value="CANCELADO">CANCELADO</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px] font-semibold">
              <th className="py-3 px-4">Número</th>
              <th className="py-3 px-4">Cliente</th>
              <th className="py-3 px-4">Data</th>
              <th className="py-3 px-4">Total</th>
              <th className="py-3 px-4">Situação</th>
              <th className="py-3 px-4">Origem</th>
              <th className="py-3 px-4 text-right">Detalhes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {orders.map((o) => {
              const statusColor =
                o.SITUACAO === 'APROVADO'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200/70'
                  : o.SITUACAO === 'FATURADO'
                  ? 'bg-purple-50 text-purple-700 border-purple-200/70'
                  : o.SITUACAO === 'ENTREGUE'
                  ? 'bg-teal-50 text-teal-700 border-teal-200/70'
                  : o.SITUACAO === 'CANCELADO'
                  ? 'bg-red-50 text-red-700 border-red-200/70'
                  : 'bg-blue-50 text-blue-700 border-blue-200/70';

              return (
                <tr key={o.ID} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-sky-800">{o.NUMERO}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{o.CLIENTE_NOME}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{o.DT_PEDIDO}</td>
                  <td className="py-3 px-4 font-mono font-bold text-emerald-700">
                    R$ {o.TOTAL.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${statusColor}`}>
                      {o.SITUACAO}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{o.ORIGEM}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => setDetailOrder(o)}
                      className="p-1.5 rounded-lg bg-sky-50 border border-sky-200/80 text-sky-700 hover:bg-sky-100 transition-colors shadow-2xs"
                      title="Visualizar Detalhes do Pedido"
                    >
                      <Eye className="w-4 h-4 inline" />
                    </button>
                  </td>
                </tr>
              );
            })}
            {orders.length === 0 && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-400">
                  Nenhum pedido registrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de Detalhamento do Pedido */}
      {detailOrder && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  Pedido {detailOrder.NUMERO} — {detailOrder.CLIENTE_NOME}
                </h2>
                <p className="text-slate-500">
                  Emissão: {detailOrder.DT_PEDIDO} • Origem: {detailOrder.ORIGEM} • ID Bling:{' '}
                  {detailOrder.ID_EXT || 'Local'}
                </p>
              </div>
              <button type="button" onClick={() => setDetailOrder(null)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <span className="font-semibold text-slate-600">Alterar Situação:</span>
              {(['ABERTO', 'APROVADO', 'FATURADO', 'ENTREGUE', 'CANCELADO'] as const).map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => void handleStatusChange(detailOrder.ID, st)}
                  className={`px-2.5 py-1 rounded-lg font-bold text-[11px] ${
                    detailOrder.SITUACAO === st
                      ? 'bg-[#0F3D6E] text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <table className="w-full text-left border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50">
                <tr>
                  <th className="p-2.5">Código</th>
                  <th className="p-2.5">Produto</th>
                  <th className="p-2.5">Qtd</th>
                  <th className="p-2.5">Preço Unit.</th>
                  <th className="p-2.5">Desconto</th>
                  <th className="p-2.5 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(detailOrder.ITEMS || []).map((it, idx) => (
                  <tr key={idx}>
                    <td className="p-2.5 font-mono">{it.CODIGO_PRD}</td>
                    <td className="p-2.5 font-semibold">{it.NOME_PRD}</td>
                    <td className="p-2.5 font-mono">{it.QUANTIDADE}</td>
                    <td className="p-2.5 font-mono">R$ {it.PRECO_UNIT.toFixed(2)}</td>
                    <td className="p-2.5 font-mono">R$ {(it.DESC_VALOR || 0).toFixed(2)}</td>
                    <td className="p-2.5 font-mono font-bold text-right">
                      R$ {(it.SUBTOTAL || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="grid grid-cols-4 gap-3 p-3 rounded-xl bg-slate-50 font-mono">
              <div>
                <span className="text-slate-400 block">Subtotal</span>
                <strong>R$ {detailOrder.SUBTOTAL.toFixed(2)}</strong>
              </div>
              <div>
                <span className="text-slate-400 block">Descontos</span>
                <strong className="text-amber-700">- R$ {detailOrder.DESCONTO.toFixed(2)}</strong>
              </div>
              <div>
                <span className="text-slate-400 block">Frete</span>
                <strong>+ R$ {detailOrder.FRETE.toFixed(2)}</strong>
              </div>
              <div>
                <span className="text-slate-400 block">Total Final</span>
                <strong className="text-base text-emerald-700">
                  R$ {detailOrder.TOTAL.toFixed(2)}
                </strong>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Criação de Pedido */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateOrder}
            className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold flex items-center gap-2">
                <ShoppingCart className="w-5 h-5 text-sky-600" /> Emitir Novo Pedido de Venda
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
                      {c.NOME} ({c.CODIGO})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Condição de Pagamento</label>
                <input
                  type="text"
                  value={condPagto}
                  onChange={(e) => setCondPagto(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-700">Itens do Pedido</span>
                <button
                  type="button"
                  onClick={addItemRow}
                  className="text-sky-700 font-semibold hover:underline"
                >
                  + Adicionar Produto
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
                      step="1"
                      value={item.QUANTIDADE}
                      onChange={(e) => {
                        const copy = [...items];
                        copy[idx].QUANTIDADE = Number(e.target.value);
                        setItems(copy);
                      }}
                      placeholder="Qtd"
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
                      placeholder="Preço"
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
                      className="text-red-600 p-1"
                    >
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-3 gap-3 items-end bg-slate-100 p-3 rounded-xl">
              <div>
                <label className="font-semibold block mb-1">Frete (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  value={frete}
                  onChange={(e) => setFrete(Number(e.target.value))}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded bg-white font-mono"
                />
              </div>
              <div className="text-right font-mono">
                <span className="text-slate-500 block">Subtotal: R$ {subtotal.toFixed(2)}</span>
                <span className="text-amber-700 block">Descontos: - R$ {totalDiscount.toFixed(2)}</span>
              </div>
              <div className="text-right font-mono">
                <span className="text-slate-500 block">Total do Pedido</span>
                <strong className="text-lg text-emerald-700">R$ {finalTotal.toFixed(2)}</strong>
              </div>
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
                className="px-5 py-2 rounded-lg bg-[#0F3D6E] text-white font-semibold"
              >
                Emitir Pedido
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

