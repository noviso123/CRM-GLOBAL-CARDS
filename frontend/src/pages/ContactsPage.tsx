import React, { useEffect, useState } from 'react';
import { Plus, Search, Trash2, UserCheck, X } from 'lucide-react';
import { apiRequest } from '../services/api';
import { ClientRecord, ContactRecord, PaginatedResponse } from '../types/crm';

export const ContactsPage: React.FC = () => {
  const [contacts, setContacts] = useState<ContactRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [search, setSearch] = useState('');
  const [clientFilter, setClientFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    ID_CLIENTE: '',
    NOME: '',
    CARGO: '',
    DEPTO: '',
    TELEFONE: '',
    CELULAR: '',
    EMAIL: '',
    PRINCIPAL: true,
    OBS: '',
  });

  const loadData = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (clientFilter) params.set('client_id', clientFilter);
      const [cRes, cliRes] = await Promise.all([
        apiRequest<PaginatedResponse<ContactRecord>>(`/contacts?${params.toString()}`),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=200'),
      ]);
      setContacts(cRes.items);
      setClients(cliRes.items);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadData();
  }, [search, clientFilter]);

  const clientMap = Object.fromEntries(clients.map((c) => [c.ID, c.NOME]));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiRequest('/contacts', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      setModalOpen(false);
      setForm({
        ID_CLIENTE: '',
        NOME: '',
        CARGO: '',
        DEPTO: '',
        TELEFONE: '',
        CELULAR: '',
        EMAIL: '',
        PRINCIPAL: true,
        OBS: '',
      });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiRequest(`/contacts/${id}`, { method: 'DELETE' });
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Módulo de Contatos</h1>
          <p className="text-xs text-slate-500">
            Pessoas de contato, compradores e decisores vinculados aos clientes.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0F3D6E] text-white text-xs font-semibold"
        >
          <Plus className="w-4 h-4" /> Novo Contato
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar contato por nome, cargo, e-mail ou celular..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg"
          />
        </div>
        <select
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value)}
          className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white"
        >
          <option value="">Todos os clientes</option>
          {clients.map((c) => (
            <option key={c.ID} value={c.ID}>
              {c.NOME}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px]">
              <th className="py-3 px-4">Nome</th>
              <th className="py-3 px-4">Cliente Relacionado</th>
              <th className="py-3 px-4">Cargo / Depto</th>
              <th className="py-3 px-4">E-mail</th>
              <th className="py-3 px-4">Telefone / Celular</th>
              <th className="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {contacts.map((ct) => (
              <tr key={ct.ID} className="hover:bg-slate-50">
                <td className="py-3 px-4 font-semibold text-slate-900">
                  {ct.NOME}{' '}
                  {ct.PRINCIPAL && (
                    <span className="ml-1 px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 text-[10px]">
                      Principal
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 text-slate-700">
                  {clientMap[ct.ID_CLIENTE] || ct.ID_CLIENTE}
                </td>
                <td className="py-3 px-4 text-slate-600">
                  {ct.CARGO || '—'} {ct.DEPTO ? `(${ct.DEPTO})` : ''}
                </td>
                <td className="py-3 px-4">{ct.EMAIL || '—'}</td>
                <td className="py-3 px-4 font-mono">{ct.CELULAR || ct.TELEFONE || '—'}</td>
                <td className="py-3 px-4 text-right">
                  <button
                    type="button"
                    onClick={() => void handleDelete(ct.ID)}
                    className="p-1.5 rounded text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
            {contacts.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400">
                  Nenhum contato registrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h2 className="text-base font-bold flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-sky-600" /> Novo Contato
              </h2>
              <button type="button" onClick={() => setModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <form onSubmit={handleSave} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Cliente Relacionado *</label>
                <select
                  required
                  value={form.ID_CLIENTE}
                  onChange={(e) => setForm({ ...form, ID_CLIENTE: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">Selecione um cliente...</option>
                  {clients.map((c) => (
                    <option key={c.ID} value={c.ID}>
                      {c.NOME} ({c.CODIGO})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Nome do Contato *</label>
                <input
                  type="text"
                  required
                  value={form.NOME}
                  onChange={(e) => setForm({ ...form, NOME: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">Cargo</label>
                  <input
                    type="text"
                    value={form.CARGO}
                    onChange={(e) => setForm({ ...form, CARGO: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Departamento</label>
                  <input
                    type="text"
                    value={form.DEPTO}
                    onChange={(e) => setForm({ ...form, DEPTO: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold block mb-1">E-mail</label>
                  <input
                    type="email"
                    value={form.EMAIL}
                    onChange={(e) => setForm({ ...form, EMAIL: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Celular / WhatsApp</label>
                  <input
                    type="text"
                    value={form.CELULAR}
                    onChange={(e) => setForm({ ...form, CELULAR: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 font-semibold"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-[#0F3D6E] text-white font-semibold"
                >
                  Salvar Contato
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

