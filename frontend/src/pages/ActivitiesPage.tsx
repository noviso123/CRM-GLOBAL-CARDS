import React, { useEffect, useState } from 'react';
import { Calendar, CheckCircle2, Clock, List, Plus, X, XCircle } from 'lucide-react';
import { apiRequest } from '../services/api';
import { ActivityRecord, ClientRecord, PaginatedResponse } from '../types/crm';

export const ActivitiesPage: React.FC = () => {
  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
  const [situacaoFilter, setSituacaoFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    TITULO: '',
    DESCRICAO: '',
    TIPO: 'LIGACAO',
    ID_CLIENTE: '',
    DATA_AG: '2026-11-05',
    HORA_AG: '10:00',
    PRIORIDADE: 'ALTA',
  });

  const loadData = async () => {
    try {
      const params = new URLSearchParams();
      if (situacaoFilter) params.set('situacao', situacaoFilter);
      const [aRes, cRes] = await Promise.all([
        apiRequest<PaginatedResponse<ActivityRecord>>(`/activities?${params.toString()}`),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=200'),
      ]);
      setActivities(aRes.items);
      setClients(cRes.items);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadData();
  }, [situacaoFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/activities', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      setModalOpen(false);
      setForm({
        TITULO: '',
        DESCRICAO: '',
        TIPO: 'LIGACAO',
        ID_CLIENTE: '',
        DATA_AG: '2026-11-05',
        HORA_AG: '10:00',
        PRIORIDADE: 'ALTA',
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleComplete = async (id: string) => {
    await apiRequest(`/activities/${id}/complete`, { method: 'PATCH' });
    await loadData();
  };

  const handleCancel = async (id: string) => {
    await apiRequest(`/activities/${id}/cancel`, { method: 'PATCH' });
    await loadData();
  };

  // Agrupamento por data para a visão de Calendário
  const groupedByDate = activities.reduce<Record<string, ActivityRecord[]>>((acc, act) => {
    const key = act.DATA_AG || 'Sem data';
    acc[key] = acc[key] || [];
    acc[key].push(act);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Atividades e Acompanhamento</h1>
          <p className="text-xs text-slate-500">
            Agenda comercial de ligações, reuniões, retornos e tarefas em lista ou calendário.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex border border-slate-200 rounded-lg overflow-hidden bg-white">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-1 ${
                viewMode === 'list' ? 'bg-[#053679] text-white' : 'text-slate-600'
              }`}
            >
              <List className="w-3.5 h-3.5" /> Lista
            </button>
            <button
              type="button"
              onClick={() => setViewMode('calendar')}
              className={`px-3 py-1.5 text-xs font-semibold flex items-center gap-1 ${
                viewMode === 'calendar' ? 'bg-[#053679] text-white' : 'text-slate-600'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" /> Calendário
            </button>
          </div>
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#053679] text-white text-xs font-semibold"
          >
            <Plus className="w-4 h-4" /> Nova Atividade
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="flex gap-2">
        {['', 'PENDENTE', 'CONCLUIDA', 'CANCELADA'].map((st) => (
          <button
            key={st || 'ALL'}
            type="button"
            onClick={() => setSituacaoFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${
              situacaoFilter === st
                ? 'bg-[#053679] text-white border-[#053679]'
                : 'bg-white text-slate-600 border-slate-200'
            }`}
          >
            {st || 'Todas'}
          </button>
        ))}
      </div>

      {viewMode === 'list' ? (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px]">
                <th className="py-3 px-4">Título</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">Cliente</th>
                <th className="py-3 px-4">Data / Hora</th>
                <th className="py-3 px-4">Prioridade</th>
                <th className="py-3 px-4">Situação</th>
                <th className="py-3 px-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {activities.map((a) => (
                <tr key={a.ID} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-bold text-slate-900">{a.TITULO}</td>
                  <td className="py-3 px-4">{a.TIPO}</td>
                  <td className="py-3 px-4">{a.CLIENTE_NOME || '—'}</td>
                  <td className="py-3 px-4 font-mono">
                    {a.DATA_AG} às {a.HORA_AG}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 font-bold text-[10px]">
                      {a.PRIORIDADE}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-semibold">{a.SITUACAO}</td>
                  <td className="py-3 px-4 text-right space-x-1">
                    {a.SITUACAO === 'PENDENTE' && (
                      <>
                        <button
                          type="button"
                          onClick={() => void handleComplete(a.ID)}
                          className="p-1.5 rounded text-emerald-700 hover:bg-emerald-50"
                          title="Concluir atividade"
                        >
                          <CheckCircle2 className="w-4 h-4 inline" />
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleCancel(a.ID)}
                          className="p-1.5 rounded text-red-600 hover:bg-red-50"
                          title="Cancelar atividade"
                        >
                          <XCircle className="w-4 h-4 inline" />
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {activities.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Nenhuma atividade registrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(groupedByDate).map(([dateKey, list]) => (
            <div
              key={dateKey}
              className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-2"
            >
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-[#053679] border-b border-slate-100 pb-2">
                <Clock className="w-4 h-4" /> {dateKey}
              </div>
              {list.map((a) => (
                <div key={a.ID} className="p-2.5 rounded-lg bg-slate-50 text-xs space-y-1">
                  <div className="flex justify-between font-bold text-slate-800">
                    <span>{a.TITULO}</span>
                    <span className="font-mono text-sky-700">{a.HORA_AG}</span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {a.TIPO} • {a.CLIENTE_NOME || 'Geral'} • {a.SITUACAO}
                  </p>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <form
            onSubmit={handleCreate}
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-3 text-xs"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold">Agendar Atividade Comercial</h2>
              <button type="button" onClick={() => setModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div>
              <label className="font-semibold block mb-1">Título *</label>
              <input
                type="text"
                required
                value={form.TITULO}
                onChange={(e) => setForm({ ...form, TITULO: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Tipo</label>
                <select
                  value={form.TIPO}
                  onChange={(e) => setForm({ ...form, TIPO: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  {[
                    'LIGACAO',
                    'REUNIAO',
                    'EMAIL',
                    'RETORNO',
                    'ATENDIMENTO',
                    'NEGOCIACAO',
                    'TAREFA',
                    'OUTROS',
                  ].map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Prioridade</label>
                <select
                  value={form.PRIORIDADE}
                  onChange={(e) => setForm({ ...form, PRIORIDADE: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="BAIXA">BAIXA</option>
                  <option value="MEDIA">MEDIA</option>
                  <option value="ALTA">ALTA</option>
                  <option value="URGENTE">URGENTE</option>
                </select>
              </div>
            </div>
            <div>
              <label className="font-semibold block mb-1">Cliente Relacionado</label>
              <select
                value={form.ID_CLIENTE}
                onChange={(e) => setForm({ ...form, ID_CLIENTE: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
              >
                <option value="">Opcional...</option>
                {clients.map((c) => (
                  <option key={c.ID} value={c.ID}>
                    {c.NOME}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold block mb-1">Data *</label>
                <input
                  type="date"
                  required
                  value={form.DATA_AG}
                  onChange={(e) => setForm({ ...form, DATA_AG: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Horário</label>
                <input
                  type="time"
                  value={form.HORA_AG}
                  onChange={(e) => setForm({ ...form, HORA_AG: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-3">
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
                Agendar
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};


