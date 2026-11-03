import React, { useEffect, useState } from 'react';
import { Briefcase, Kanban, List, Plus, Settings2, X } from 'lucide-react';
import { apiRequest } from '../services/api';
import {
  ClientRecord,
  FunnelRecord,
  OpportunityRecord,
  PaginatedResponse,
} from '../types/crm';

export const OpportunitiesFunnelPage: React.FC<{ defaultView?: 'kanban' | 'list' }> = ({
  defaultView = 'kanban',
}) => {
  const [funnels, setFunnels] = useState<FunnelRecord[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [viewMode, setViewMode] = useState<'kanban' | 'list'>(defaultView);
  const [modalOpen, setModalOpen] = useState(false);
  const [stageModalOpen, setStageModalOpen] = useState(false);
  const [draggedOppId, setDraggedOppId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    TITULO: '',
    ID_CLIENTE: '',
    ID_ETAPA: '',
    VALOR_EST: 2500,
    DT_PREV: '2026-12-10',
    PROX_ATIV: 'Apresentar proposta comercial',
    ORIGEM: 'WHATSAPP',
    OBS: '',
  });

  const [newStage, setNewStage] = useState({
    NOME: '',
    ORDEM: 5,
    COR: '#0284C7',
    PROB_PAD: 50,
    TIPO_ETAPA: 'ABERTA',
  });

  const loadFunnelData = async () => {
    try {
      const [fRes, oRes, cRes] = await Promise.all([
        apiRequest<FunnelRecord[]>('/opportunities/funnels'),
        apiRequest<PaginatedResponse<OpportunityRecord>>('/opportunities?page_size=200'),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=200'),
      ]);
      setFunnels(fRes);
      setOpportunities(oRes.items);
      setClients(cRes.items);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    setViewMode(defaultView);
  }, [defaultView]);

  useEffect(() => {
    void loadFunnelData();
  }, []);

  const activeFunnel = funnels[0];
  const stages = activeFunnel?.stages || [];

  const handleMoveStage = async (oppId: string, targetStageId: string) => {
    try {
      await apiRequest(`/opportunities/${oppId}/stage`, {
        method: 'PATCH',
        body: JSON.stringify({ ID_ETAPA: targetStageId }),
      });
      await loadFunnelData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateOpp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/opportunities', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          ID_FUNIL: activeFunnel?.ID || '',
          ID_ETAPA: form.ID_ETAPA || stages[0]?.ID || '',
        }),
      });
      setModalOpen(false);
      setForm({
        TITULO: '',
        ID_CLIENTE: '',
        ID_ETAPA: '',
        VALOR_EST: 2500,
        DT_PREV: '2026-12-10',
        PROX_ATIV: 'Apresentar proposta comercial',
        ORIGEM: 'WHATSAPP',
        OBS: '',
      });
      await loadFunnelData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreateStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFunnel) return;
    try {
      await apiRequest('/opportunities/funnels/stages', {
        method: 'POST',
        body: JSON.stringify({ ...newStage, ID_FUNIL: activeFunnel.ID }),
      });
      setStageModalOpen(false);
      setNewStage({ NOME: '', ORDEM: stages.length + 1, COR: '#0284C7', PROB_PAD: 50, TIPO_ETAPA: 'ABERTA' });
      await loadFunnelData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Funil de Vendas & Oportunidades Comerciais
          </h1>
          <p className="text-xs text-slate-500">
            Arraste cards entre etapas ou selecione diretamente. Toda mudança de etapa gera registro automático em HISTORIC.DBF.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100/80 p-1 rounded-xl border border-slate-200/80 shadow-2xs">
            <button
              type="button"
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all ${
                viewMode === 'kanban' ? 'bg-[#053679] text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Kanban className="w-3.5 h-3.5" /> Kanban
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all ${
                viewMode === 'list' ? 'bg-[#053679] text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <List className="w-3.5 h-3.5" /> Lista
            </button>
          </div>
          <button
            type="button"
            onClick={() => setStageModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs transition-colors"
          >
            <Settings2 className="w-4 h-4" /> + Etapa
          </button>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#053679] hover:bg-[#042A5F] text-white text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" /> Nova Oportunidade
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      {viewMode === 'kanban' ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => {
            const stageOpps = opportunities.filter((o) => o.ID_ETAPA === stage.ID);
            const stageTotal = stageOpps.reduce((acc, o) => acc + o.VALOR_EST, 0);
            return (
              <div
                key={stage.ID}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (draggedOppId) {
                    void handleMoveStage(draggedOppId, stage.ID);
                    setDraggedOppId(null);
                  }
                }}
                className="w-80 shrink-0 bg-slate-100/90 rounded-2xl border border-slate-200/90 p-3.5 flex flex-col max-h-[75vh] shadow-2xs"
              >
                <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-slate-200/80 bg-white/70 px-2.5 py-1.5 rounded-xl border border-slate-200/40">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full shrink-0 shadow-2xs"
                      style={{ backgroundColor: stage.COR }}
                    />
                    <span className="text-xs font-bold text-slate-800">{stage.NOME}</span>
                    <span className="px-1.5 py-0.5 rounded-full bg-white text-[10px] font-bold text-slate-600 shadow-2xs">
                      {stageOpps.length}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-slate-700">
                    R$ {stageTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>

                <div className="space-y-2.5 overflow-y-auto flex-1 pr-1">
                  {stageOpps.map((op) => (
                    <div
                      key={op.ID}
                      draggable
                      onDragStart={() => setDraggedOppId(op.ID)}
                      className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-slate-900 leading-snug">
                          {op.TITULO}
                        </h4>
                        <span className="px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 font-mono text-[10px] font-bold shrink-0 border border-sky-100">
                          {op.PROBABIL}%
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 font-medium">
                        {op.CLIENTE_NOME || 'Cliente'}
                      </p>
                      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                        <span className="font-mono text-xs font-extrabold text-[#053679]">
                          R$ {op.VALOR_EST.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                        <select
                          value={op.ID_ETAPA}
                          onChange={(e) => void handleMoveStage(op.ID, e.target.value)}
                          className="text-[10px] border border-slate-200 rounded px-1.5 py-0.5 bg-slate-50 text-slate-700"
                        >
                          {stages.map((st) => (
                            <option key={st.ID} value={st.ID}>
                              {st.NOME}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))}
                  {stageOpps.length === 0 && (
                    <div className="py-8 text-center text-[11px] text-slate-400 border border-dashed border-slate-200 rounded-lg">
                      Arraste oportunidades para esta etapa
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px]">
                <th className="py-3 px-4">Oportunidade</th>
                <th className="py-3 px-4">Cliente</th>
                <th className="py-3 px-4">Etapa</th>
                <th className="py-3 px-4">Valor Estimado</th>
                <th className="py-3 px-4">Probabilidade</th>
                <th className="py-3 px-4">Origem</th>
                <th className="py-3 px-4">Situação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {opportunities.map((op) => (
                <tr key={op.ID} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-bold text-slate-900">{op.TITULO}</td>
                  <td className="py-3 px-4">{op.CLIENTE_NOME}</td>
                  <td className="py-3 px-4">
                    <span
                      className="px-2 py-0.5 rounded text-white text-[10px] font-bold"
                      style={{ backgroundColor: op.ETAPA_COR || '#0284C7' }}
                    >
                      {op.ETAPA_NOME}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono font-bold">
                    R$ {op.VALOR_EST.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 font-mono">{op.PROBABIL}%</td>
                  <td className="py-3 px-4">{op.ORIGEM}</td>
                  <td className="py-3 px-4 font-semibold">{op.SITUACAO}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Nova Oportunidade */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateOpp}
            className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-3 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-sky-600" /> Nova Oportunidade Comercial
              </h2>
              <button type="button" onClick={() => setModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div>
              <label className="font-semibold block mb-1">Título da Oportunidade *</label>
              <input
                type="text"
                required
                value={form.TITULO}
                onChange={(e) => setForm({ ...form, TITULO: e.target.value })}
                placeholder="Ex: Fornecimento 1.000 Crachás PVC + Cordões"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="font-semibold block mb-1">Cliente *</label>
              <select
                required
                value={form.ID_CLIENTE}
                onChange={(e) => setForm({ ...form, ID_CLIENTE: e.target.value })}
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
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Etapa Inicial</label>
                <select
                  value={form.ID_ETAPA}
                  onChange={(e) => setForm({ ...form, ID_ETAPA: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  {stages.map((st) => (
                    <option key={st.ID} value={st.ID}>
                      {st.NOME}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Valor Estimado (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  value={form.VALOR_EST}
                  onChange={(e) => setForm({ ...form, VALOR_EST: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono"
                />
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
                className="px-5 py-2 rounded-lg bg-[#053679] text-white font-semibold"
              >
                Criar Oportunidade
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Modal Configurar Nova Etapa */}
      {stageModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreateStage}
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-3 text-xs"
          >
            <h3 className="text-base font-bold text-slate-900">Nova Etapa do Funil</h3>
            <div>
              <label className="font-semibold block mb-1">Nome da Etapa *</label>
              <input
                type="text"
                required
                value={newStage.NOME}
                onChange={(e) => setNewStage({ ...newStage, NOME: e.target.value })}
                placeholder="Ex: Amostra Enviada"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Ordem</label>
                <input
                  type="number"
                  value={newStage.ORDEM}
                  onChange={(e) => setNewStage({ ...newStage, ORDEM: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Probabilidade (%)</label>
                <input
                  type="number"
                  value={newStage.PROB_PAD}
                  onChange={(e) => setNewStage({ ...newStage, PROB_PAD: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-3">
              <button
                type="button"
                onClick={() => setStageModalOpen(false)}
                className="px-4 py-2 rounded-lg border border-slate-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-[#053679] text-white font-semibold"
              >
                Adicionar Etapa
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};


