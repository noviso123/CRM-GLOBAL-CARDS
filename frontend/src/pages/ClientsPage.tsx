import React, { useEffect, useState } from 'react';
import {
  Building2,
  Download,
  Edit3,
  Eye,
  Plus,
  Search,
  Trash2,
  UserPlus,
  X,
} from 'lucide-react';
import { apiRequest, downloadAuthorizedCsv } from '../services/api';
import {
  ActivityRecord,
  AddressRecord,
  ClientRecord,
  ContactRecord,
  ConversationRecord,
  HistoryRecord,
  OpportunityRecord,
  OrderRecord,
  PaginatedResponse,
  QuotationRecord,
} from '../types/crm';

interface ClientOverviewData {
  client: ClientRecord;
  contacts: ContactRecord[];
  addresses: AddressRecord[];
  orders: OrderRecord[];
  quotations: QuotationRecord[];
  opportunities: OpportunityRecord[];
  conversations: ConversationRecord[];
  activities: ActivityRecord[];
  history: HistoryRecord[];
  notes: { content?: string; updated_at?: string };
}

const INITIAL_FORM = {
  TIPO_PES: 'PJ',
  NOME: '',
  FANTASIA: '',
  CPF_CNPJ: '',
  INSC_EST: '',
  EMAIL: '',
  TELEFONE: '',
  CELULAR: '',
  ENDERECO: '',
  NUMERO: '',
  COMPLEM: '',
  BAIRRO: '',
  CIDADE: '',
  UF: 'SP',
  CEP: '',
  PAIS: 'Brasil',
  OBS_CURTA: '',
  OBSERVACOES_LONGAS: '',
  SITUACAO: 'ATIVO',
  ORIGEM: 'LOCAL',
};

export const ClientsPage: React.FC = () => {
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [situacaoFilter, setSituacaoFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(INITIAL_FORM);
  const [error, setError] = useState<string | null>(null);

  // Detalhamento Individual com 10 abas
  const [overview, setOverview] = useState<ClientOverviewData | null>(null);
  const [activeTab, setActiveTab] = useState<number>(1);
  const [newAddress, setNewAddress] = useState({
    TIPO_END: 'ENTREGA',
    ENDERECO: '',
    NUMERO: '',
    BAIRRO: '',
    CIDADE: '',
    UF: 'SP',
    CEP: '',
  });

  const loadClients = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (situacaoFilter) params.set('situacao', situacaoFilter);
      const res = await apiRequest<PaginatedResponse<ClientRecord>>(
        `/clients?${params.toString()}`
      );
      setClients(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    void loadClients();
  }, [search, situacaoFilter]);

  const openDetails = async (clientId: string) => {
    try {
      const data = await apiRequest<ClientOverviewData>(`/clients/${clientId}/overview`);
      setOverview(data);
      setActiveTab(1);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (editingId) {
        await apiRequest(`/clients/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(form),
        });
      } else {
        await apiRequest('/clients', {
          method: 'POST',
          body: JSON.stringify(form),
        });
      }
      setModalOpen(false);
      setEditingId(null);
      setForm(INITIAL_FORM);
      await loadClients();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (id: string) => {
    setError(null);
    try {
      await apiRequest(`/clients/${id}`, { method: 'DELETE' });
      await loadClients();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overview) return;
    try {
      await apiRequest(`/clients/${overview.client.ID}/addresses`, {
        method: 'POST',
        body: JSON.stringify(newAddress),
      });
      setNewAddress({
        TIPO_END: 'ENTREGA',
        ENDERECO: '',
        NUMERO: '',
        BAIRRO: '',
        CIDADE: '',
        UF: 'SP',
        CEP: '',
      });
      await openDetails(overview.client.ID);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Gestão de Clientes</h1>
          <p className="text-xs text-slate-500">
            Base completa PF e PJ ({total} registros em CLIENTES.DBF) com histórico 360º.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => void downloadAuthorizedCsv('/clients/export/csv', 'clientes_globalcards.csv')}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs"
          >
            <Download className="w-4 h-4" /> Exportar CSV
          </button>
          <button
            type="button"
            onClick={() => {
              setEditingId(null);
              setForm(INITIAL_FORM);
              setModalOpen(true);
            }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0F3D6E] hover:bg-[#0B2D52] text-white text-xs font-semibold shadow-sm"
          >
            <Plus className="w-4 h-4" /> Novo Cliente
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex justify-between">
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} className="font-bold">
            ✕
          </button>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar por código, razão social, nome fantasia, CPF/CNPJ, e-mail ou cidade..."
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-sky-600"
          />
        </div>
        <select
          value={situacaoFilter}
          onChange={(e) => setSituacaoFilter(e.target.value)}
          className="px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white"
        >
          <option value="">Todas as situações</option>
          <option value="ATIVO">ATIVO</option>
          <option value="PROSPECT">PROSPECT</option>
          <option value="INATIVO">INATIVO</option>
          <option value="BLOQUEADO">BLOQUEADO</option>
        </select>
      </div>

      {/* Tabela de Clientes */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[11px]">
              <th className="py-3 px-4">Código</th>
              <th className="py-3 px-4">Nome / Razão Social</th>
              <th className="py-3 px-4">CPF / CNPJ</th>
              <th className="py-3 px-4">Contato</th>
              <th className="py-3 px-4">Cidade/UF</th>
              <th className="py-3 px-4">Situação</th>
              <th className="py-3 px-4">Origem</th>
              <th className="py-3 px-4 text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {clients.map((c) => (
              <tr key={c.ID} className="hover:bg-slate-50/90">
                <td className="py-3 px-4 font-mono font-semibold text-sky-800">{c.CODIGO}</td>
                <td className="py-3 px-4">
                  <div className="font-semibold text-slate-900">{c.NOME}</div>
                  {c.FANTASIA && <div className="text-[11px] text-slate-500">{c.FANTASIA}</div>}
                </td>
                <td className="py-3 px-4 font-mono text-slate-600">{c.CPF_CNPJ || '—'}</td>
                <td className="py-3 px-4">
                  <div>{c.EMAIL || '—'}</div>
                  <div className="text-slate-500">{c.CELULAR || c.TELEFONE || ''}</div>
                </td>
                <td className="py-3 px-4">
                  {c.CIDADE ? `${c.CIDADE}/${c.UF}` : '—'}
                </td>
                <td className="py-3 px-4">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      c.SITUACAO === 'ATIVO'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {c.SITUACAO}
                  </span>
                </td>
                <td className="py-3 px-4 font-medium text-slate-600">{c.ORIGEM}</td>
                <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => void openDetails(c.ID)}
                    className="p-1.5 rounded-lg bg-sky-50 border border-sky-200/80 text-sky-700 hover:bg-sky-100 transition-colors shadow-2xs"
                    title="Abrir Visão 360º (10 Abas)"
                  >
                    <Eye className="w-4 h-4 inline" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(c.ID);
                      setForm({
                        ...INITIAL_FORM,
                        ...c,
                        OBSERVACOES_LONGAS: c.OBS_CURTA || '',
                      });
                      setModalOpen(true);
                    }}
                    className="p-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors shadow-2xs"
                    title="Editar Cliente"
                  >
                    <Edit3 className="w-4 h-4 inline" />
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDelete(c.ID)}
                    className="p-1.5 rounded-lg bg-red-50 border border-red-200/80 text-red-600 hover:bg-red-100 transition-colors shadow-2xs"
                    title="Excluir Cliente"
                  >
                    <Trash2 className="w-4 h-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
            {clients.length === 0 && (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  Nenhum cliente encontrado. Clique em &ldquo;Novo Cliente&rdquo; para cadastrar.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Página/Modal de Detalhamento Individual com as 10 Abas Obrigatórias */}
      {overview && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 bg-[#0F3D6E] text-white flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Building2 className="w-6 h-6 text-sky-300" />
                <div>
                  <h2 className="text-base font-bold">
                    {overview.client.NOME}{' '}
                    <span className="font-mono text-xs text-sky-200">
                      ({overview.client.CODIGO})
                    </span>
                  </h2>
                  <p className="text-xs text-sky-200">
                    CPF/CNPJ: {overview.client.CPF_CNPJ || 'Não informado'} • Última interação:{' '}
                    {overview.client.DT_ULT_INT || overview.client.DT_ATUA}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setOverview(null)}
                className="p-1.5 rounded-lg hover:bg-white/10"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navegação das 10 Abas */}
            <div className="flex overflow-x-auto border-b border-slate-200 bg-slate-50 px-4">
              {[
                [1, '1. Dados Cadastrais'],
                [2, `2. Contatos (${overview.contacts.length})`],
                [3, `3. Endereços (${overview.addresses.length})`],
                [4, `4. Pedidos (${overview.orders.length})`],
                [5, `5. Orçamentos (${overview.quotations.length})`],
                [6, `6. Oportunidades (${overview.opportunities.length})`],
                [7, `7. Conversas (${overview.conversations.length})`],
                [8, `8. Atividades (${overview.activities.length})`],
                [9, `9. Histórico (${overview.history.length})`],
                [10, '10. Observações'],
              ].map(([idx, label]) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setActiveTab(Number(idx))}
                  className={`px-3.5 py-3 text-xs font-semibold whitespace-nowrap border-b-2 transition ${
                    activeTab === idx
                      ? 'border-sky-600 text-sky-700 bg-white'
                      : 'border-transparent text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="p-6 overflow-y-auto flex-1 text-xs space-y-4">
              {activeTab === 1 && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">Razão Social / Nome</span>
                    <strong className="text-slate-900">{overview.client.NOME}</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">Nome Fantasia</span>
                    <strong className="text-slate-900">{overview.client.FANTASIA || '—'}</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">Tipo / CPF-CNPJ</span>
                    <strong className="text-slate-900">
                      {overview.client.TIPO_PES} • {overview.client.CPF_CNPJ || '—'}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">E-mail</span>
                    <strong className="text-slate-900">{overview.client.EMAIL || '—'}</strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">Telefones</span>
                    <strong className="text-slate-900">
                      {overview.client.TELEFONE} / {overview.client.CELULAR}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">Endereço Principal</span>
                    <strong className="text-slate-900">
                      {overview.client.ENDERECO}, {overview.client.NUMERO} -{' '}
                      {overview.client.CIDADE}/{overview.client.UF}
                    </strong>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50">
                    <span className="text-slate-400 block">ID Bling</span>
                    <strong className="text-slate-900 font-mono">
                      {overview.client.ID_EXT || 'Não vinculado'}
                    </strong>
                  </div>
                </div>
              )}

              {activeTab === 2 && (
                <div className="space-y-2">
                  {overview.contacts.map((ct) => (
                    <div
                      key={ct.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <p className="font-bold text-slate-900">{ct.NOME}</p>
                        <p className="text-slate-500">
                          {ct.CARGO} • {ct.DEPTO}
                        </p>
                      </div>
                      <div className="text-right">
                        <p>{ct.EMAIL}</p>
                        <p className="font-mono">{ct.CELULAR || ct.TELEFONE}</p>
                      </div>
                    </div>
                  ))}
                  {overview.contacts.length === 0 && (
                    <p className="text-slate-400">Nenhum contato cadastrado para este cliente.</p>
                  )}
                </div>
              )}

              {activeTab === 3 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    {overview.addresses.map((ad) => (
                      <div
                        key={ad.ID}
                        className="p-3 rounded-lg border border-slate-200 flex justify-between"
                      >
                        <div>
                          <span className="px-2 py-0.5 rounded bg-sky-50 text-sky-700 font-bold text-[10px]">
                            {ad.TIPO_END}
                          </span>
                          <p className="font-semibold text-slate-800 mt-1">
                            {ad.ENDERECO}, {ad.NUMERO} — {ad.BAIRRO}
                          </p>
                        </div>
                        <div className="text-right text-slate-600">
                          {ad.CIDADE}/{ad.UF} • CEP {ad.CEP}
                        </div>
                      </div>
                    ))}
                  </div>
                  <form
                    onSubmit={handleAddAddress}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-1 sm:grid-cols-4 gap-3"
                  >
                    <input
                      type="text"
                      required
                      placeholder="Logradouro"
                      value={newAddress.ENDERECO}
                      onChange={(e) => setNewAddress({ ...newAddress, ENDERECO: e.target.value })}
                      className="px-3 py-1.5 rounded border border-slate-300"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Número"
                      value={newAddress.NUMERO}
                      onChange={(e) => setNewAddress({ ...newAddress, NUMERO: e.target.value })}
                      className="px-3 py-1.5 rounded border border-slate-300"
                    />
                    <input
                      type="text"
                      required
                      placeholder="Cidade"
                      value={newAddress.CIDADE}
                      onChange={(e) => setNewAddress({ ...newAddress, CIDADE: e.target.value })}
                      className="px-3 py-1.5 rounded border border-slate-300"
                    />
                    <button
                      type="submit"
                      className="px-4 py-1.5 rounded bg-[#0F3D6E] text-white font-semibold"
                    >
                      + Adicionar Endereço
                    </button>
                  </form>
                </div>
              )}

              {activeTab === 4 && (
                <div className="space-y-2">
                  {overview.orders.map((ord) => (
                    <div
                      key={ord.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <span className="font-mono font-bold">{ord.NUMERO}</span>
                        <span className="ml-2 text-slate-500">Data: {ord.DT_PEDIDO}</span>
                      </div>
                      <div className="font-mono font-bold text-emerald-700">
                        R$ {ord.TOTAL.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (
                        {ord.SITUACAO})
                      </div>
                    </div>
                  ))}
                  {overview.orders.length === 0 && (
                    <p className="text-slate-400">Nenhum pedido registrado para este cliente.</p>
                  )}
                </div>
              )}

              {activeTab === 5 && (
                <div className="space-y-2">
                  {overview.quotations.map((q) => (
                    <div
                      key={q.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <span className="font-mono font-bold">{q.NUMERO}</span>
                        <span className="ml-2 text-slate-500">Validade: {q.DT_VALID}</span>
                      </div>
                      <div className="font-mono font-bold text-sky-700">
                        R$ {q.TOTAL.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (
                        {q.SITUACAO})
                      </div>
                    </div>
                  ))}
                  {overview.quotations.length === 0 && (
                    <p className="text-slate-400">Nenhum orçamento para este cliente.</p>
                  )}
                </div>
              )}

              {activeTab === 6 && (
                <div className="space-y-2">
                  {overview.opportunities.map((op) => (
                    <div
                      key={op.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <p className="font-bold text-slate-900">{op.TITULO}</p>
                        <span className="text-slate-500">Probabilidade: {op.PROBABIL}%</span>
                      </div>
                      <div className="font-mono font-bold">
                        R$ {op.VALOR_EST.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (
                        {op.SITUACAO})
                      </div>
                    </div>
                  ))}
                  {overview.opportunities.length === 0 && (
                    <p className="text-slate-400">Nenhuma oportunidade vinculada.</p>
                  )}
                </div>
              )}

              {activeTab === 7 && (
                <div className="space-y-2">
                  {overview.conversations.map((cv) => (
                    <div
                      key={cv.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <p className="font-bold">{cv.NOME_CONT} ({cv.TELEFONE})</p>
                        <p className="text-slate-500">{cv.ULT_MSG}</p>
                      </div>
                      <span className="font-semibold">{cv.SITUACAO}</span>
                    </div>
                  ))}
                  {overview.conversations.length === 0 && (
                    <p className="text-slate-400">Nenhuma conversa WhatsApp vinculada.</p>
                  )}
                </div>
              )}

              {activeTab === 8 && (
                <div className="space-y-2">
                  {overview.activities.map((ac) => (
                    <div
                      key={ac.ID}
                      className="p-3 rounded-lg border border-slate-200 flex justify-between"
                    >
                      <div>
                        <p className="font-bold">{ac.TITULO}</p>
                        <p className="text-slate-500">
                          {ac.TIPO} • {ac.DATA_AG} {ac.HORA_AG}
                        </p>
                      </div>
                      <span className="font-semibold">{ac.SITUACAO}</span>
                    </div>
                  ))}
                  {overview.activities.length === 0 && (
                    <p className="text-slate-400">Nenhuma atividade comercial vinculada.</p>
                  )}
                </div>
              )}

              {activeTab === 9 && (
                <div className="space-y-2">
                  {overview.history.map((h) => (
                    <div
                      key={h.ID}
                      className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between"
                    >
                      <div>
                        <span className="font-bold text-sky-800">[{h.ENTIDADE} • {h.ACAO}]</span>{' '}
                        <span>{h.DESCRICAO}</span>
                      </div>
                      <span className="font-mono text-slate-400">{h.DT_CRIA}</span>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 10 && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h4 className="font-bold text-slate-800 mb-2">Observações Completas do Cliente</h4>
                  <p className="whitespace-pre-wrap text-slate-700">
                    {overview.notes?.content ||
                      overview.client.OBS_CURTA ||
                      'Sem observações adicionais registradas.'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Cadastro / Edição de Cliente */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-sky-600" />
                {editingId ? 'Editar Cliente' : 'Novo Cadastro de Cliente'}
              </h2>
              <button type="button" onClick={() => setModalOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <form onSubmit={handleSave} className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Tipo Pessoa</label>
                <select
                  value={form.TIPO_PES}
                  onChange={(e) => setForm({ ...form, TIPO_PES: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="PJ">Pessoa Jurídica (PJ)</option>
                  <option value="PF">Pessoa Física (PF)</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="font-semibold block mb-1">Nome / Razão Social *</label>
                <input
                  type="text"
                  required
                  value={form.NOME}
                  onChange={(e) => setForm({ ...form, NOME: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Nome Fantasia</label>
                <input
                  type="text"
                  value={form.FANTASIA}
                  onChange={(e) => setForm({ ...form, FANTASIA: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">CPF / CNPJ</label>
                <input
                  type="text"
                  value={form.CPF_CNPJ}
                  onChange={(e) => setForm({ ...form, CPF_CNPJ: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Inscrição Estadual</label>
                <input
                  type="text"
                  value={form.INSC_EST}
                  onChange={(e) => setForm({ ...form, INSC_EST: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
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
                <label className="font-semibold block mb-1">Telefone Fixo</label>
                <input
                  type="text"
                  value={form.TELEFONE}
                  onChange={(e) => setForm({ ...form, TELEFONE: e.target.value })}
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
              <div className="sm:col-span-2">
                <label className="font-semibold block mb-1">Logradouro / Endereço</label>
                <input
                  type="text"
                  value={form.ENDERECO}
                  onChange={(e) => setForm({ ...form, ENDERECO: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Número</label>
                <input
                  type="text"
                  value={form.NUMERO}
                  onChange={(e) => setForm({ ...form, NUMERO: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Bairro</label>
                <input
                  type="text"
                  value={form.BAIRRO}
                  onChange={(e) => setForm({ ...form, BAIRRO: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Cidade</label>
                <input
                  type="text"
                  value={form.CIDADE}
                  onChange={(e) => setForm({ ...form, CIDADE: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">UF</label>
                <input
                  type="text"
                  maxLength={2}
                  value={form.UF}
                  onChange={(e) => setForm({ ...form, UF: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">CEP</label>
                <input
                  type="text"
                  value={form.CEP}
                  onChange={(e) => setForm({ ...form, CEP: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Situação</label>
                <select
                  value={form.SITUACAO}
                  onChange={(e) => setForm({ ...form, SITUACAO: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="ATIVO">ATIVO</option>
                  <option value="PROSPECT">PROSPECT</option>
                  <option value="INATIVO">INATIVO</option>
                  <option value="BLOQUEADO">BLOQUEADO</option>
                </select>
              </div>
              <div className="sm:col-span-3">
                <label className="font-semibold block mb-1">Observações Comerciais</label>
                <textarea
                  rows={3}
                  value={form.OBSERVACOES_LONGAS}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      OBS_CURTA: e.target.value.slice(0, 240),
                      OBSERVACOES_LONGAS: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div className="sm:col-span-3 flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 font-semibold text-slate-600"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-[#0F3D6E] text-white font-semibold"
                >
                  Salvar Cliente
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

