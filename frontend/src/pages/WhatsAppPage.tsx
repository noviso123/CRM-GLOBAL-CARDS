import React, { useEffect, useState } from 'react';
import {
  MessageSquare,
  Send,
  Search,
  Plus,
  Link as LinkIcon,
  Phone,
  CheckCheck,
  User,
  Target,
  X,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type {
  ConversationRecord,
  WhatsAppMessageRecord,
  ClientRecord,
  OpportunityRecord,
  PaginatedResponse,
} from '../types/crm';

export const WhatsAppPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationRecord[]>([]);
  const [selectedConv, setSelectedConv] = useState<ConversationRecord | null>(null);
  const [messages, setMessages] = useState<WhatsAppMessageRecord[]>([]);
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunityRecord[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [showNewModal, setShowNewModal] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [newForm, setNewForm] = useState({
    TELEFONE: '',
    NOME_CONT: '',
    ID_CLIENTE: '',
    ID_OPORT: '',
  });
  const [linkForm, setLinkForm] = useState({
    ID_CLIENTE: '',
    ID_OPORT: '',
    SITUACAO: 'EM_ATENDIMENTO',
    OBS_ATEND: '',
  });

  const loadConversations = async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (statusFilter) q.set('situacao', statusFilter);
      if (search) q.set('search', search);
      const [convList, cliRes, oppList] = await Promise.all([
        apiRequest<ConversationRecord[]>(`/whatsapp/conversations?${q.toString()}`),
        apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=100'),
        apiRequest<OpportunityRecord[]>('/opportunities'),
      ]);
      setConversations(convList);
      setClients(cliRes.items);
      setOpportunities(oppList);
      if (convList.length > 0 && !selectedConv) {
        selectConversation(convList[0]);
      } else if (selectedConv) {
        const updated = convList.find((c) => c.ID === selectedConv.ID);
        if (updated) setSelectedConv(updated);
      }
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (conv: ConversationRecord) => {
    setSelectedConv(conv);
    const msgs = await apiRequest<WhatsAppMessageRecord[]>(
      `/whatsapp/conversations/${conv.ID}/messages`
    );
    setMessages(msgs);
    setConversations((prev) =>
      prev.map((c) => (c.ID === conv.ID ? { ...c, NAO_LIDAS: 0 } : c))
    );
  };

  useEffect(() => {
    loadConversations();
  }, [statusFilter]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConv || !messageText.trim()) return;
    const text = messageText;
    setMessageText('');
    await apiRequest(`/whatsapp/conversations/${selectedConv.ID}/messages`, {
      method: 'POST',
      body: JSON.stringify({ CONTEUDO: text, DIRECAO: 'SAIDA', TIPO_MSG: 'TEXTO' }),
    });
    await selectConversation(selectedConv);
    await loadConversations();
  };

  const handleCreateConversation = async (e: React.FormEvent) => {
    e.preventDefault();
    const created = await apiRequest<ConversationRecord>('/whatsapp/conversations', {
      method: 'POST',
      body: JSON.stringify(newForm),
    });
    setShowNewModal(false);
    setNewForm({ TELEFONE: '', NOME_CONT: '', ID_CLIENTE: '', ID_OPORT: '' });
    await loadConversations();
    await selectConversation(created);
  };

  const openLinkModal = () => {
    if (!selectedConv) return;
    setLinkForm({
      ID_CLIENTE: selectedConv.ID_CLIENTE || '',
      ID_OPORT: selectedConv.ID_OPORT || '',
      SITUACAO: selectedConv.SITUACAO || 'EM_ATENDIMENTO',
      OBS_ATEND: selectedConv.OBS_ATEND || '',
    });
    setShowLinkModal(true);
  };

  const handleSaveLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConv) return;
    const updated = await apiRequest<ConversationRecord>(
      `/whatsapp/conversations/${selectedConv.ID}/link`,
      {
        method: 'PATCH',
        body: JSON.stringify(linkForm),
      }
    );
    setShowLinkModal(false);
    setSelectedConv(updated);
    await loadConversations();
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Atendimento & WhatsApp Comercial</h1>
          <p className="text-sm text-slate-500">
            Central de conversas integrada com vinculação direta a clientes, contatos e oportunidades.
          </p>
        </div>
        <button onClick={() => setShowNewModal(true)} className="satiro-btn-primary">
          <Plus className="w-4 h-4" /> Iniciar Atendimento
        </button>
      </div>

      <div className="satiro-card overflow-hidden grid grid-cols-1 lg:grid-cols-12 h-[640px]">
        {/* Coluna de Conversas */}
        <div className="lg:col-span-4 border-r border-slate-200 flex flex-col h-full bg-slate-50/40">
          <div className="p-3 border-b border-slate-200 space-y-2 bg-white">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadConversations()}
                placeholder="Buscar telefone ou contato..."
                className="satiro-input pl-9 py-1.5 text-xs"
              />
            </div>
            <div className="flex gap-1">
              {[
                { key: '', label: 'Todas' },
                { key: 'EM_ATENDIMENTO', label: 'Ativas' },
                { key: 'AGUARDANDO', label: 'Aguardando' },
                { key: 'ENCERRADA', label: 'Encerradas' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setStatusFilter(tab.key)}
                  className={`flex-1 py-1 text-[11px] font-semibold rounded ${
                    statusFilter === tab.key
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-200/70">
            {loading ? (
              <div className="p-6 text-center text-xs text-slate-500">Carregando conversas...</div>
            ) : conversations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                Nenhuma conversa encontrada.
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.ID}
                  onClick={() => selectConversation(conv)}
                  className={`w-full text-left p-3.5 transition-colors flex items-start gap-3 ${
                    selectedConv?.ID === conv.ID
                      ? 'bg-emerald-50/90 border-l-4 border-l-emerald-600'
                      : 'hover:bg-white'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 font-bold text-sm flex items-center justify-center shrink-0">
                    {conv.NOME_CONT.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        {conv.NOME_CONT}
                      </p>
                      <span className="text-[10px] text-slate-400">
                        {conv.DT_ULT_MSG?.slice(11, 16) || ''}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-mono">{conv.TELEFONE}</p>
                    <p className="text-xs text-slate-600 truncate mt-1">
                      {conv.ULT_MSG || 'Sem mensagens registradas'}
                    </p>
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-200/70 text-slate-700">
                        {conv.CLIENTE_NOME || 'Não vinculado'}
                      </span>
                      {conv.NAO_LIDAS > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-bold">
                          {conv.NAO_LIDAS}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Coluna de Mensagens */}
        <div className="lg:col-span-8 flex flex-col h-full bg-slate-100/60">
          {selectedConv ? (
            <>
              <div className="p-3.5 bg-white border-b border-slate-200 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center">
                    {selectedConv.NOME_CONT.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-slate-900">{selectedConv.NOME_CONT}</h3>
                      <span className="satiro-badge bg-emerald-50 text-emerald-700">
                        {selectedConv.SITUACAO}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-0.5">
                      <span className="inline-flex items-center gap-1">
                        <Phone className="w-3 h-3" /> {selectedConv.TELEFONE}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <User className="w-3 h-3 text-blue-600" />{' '}
                        {selectedConv.CLIENTE_NOME || 'Sem cliente vinculado'}
                      </span>
                      {selectedConv.OPORTUNIDADE_TITULO && (
                        <span className="inline-flex items-center gap-1">
                          <Target className="w-3 h-3 text-amber-600" />{' '}
                          {selectedConv.OPORTUNIDADE_TITULO}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button onClick={openLinkModal} className="satiro-btn-secondary py-1.5 text-xs">
                  <LinkIcon className="w-3.5 h-3.5" /> Vincular CRM / Status
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">
                    Envie uma mensagem abaixo para iniciar o histórico deste atendimento.
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isOut = msg.DIRECAO === 'SAIDA';
                    return (
                      <div
                        key={msg.ID}
                        className={`flex ${isOut ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[75%] rounded-2xl px-4 py-2.5 shadow-sm ${
                            isOut
                              ? 'bg-emerald-600 text-white rounded-br-none'
                              : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{msg.CONTEUDO}</p>
                          <div
                            className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${
                              isOut ? 'text-emerald-100' : 'text-slate-400'
                            }`}
                          >
                            <span>{msg.DT_ENVIO?.slice(11, 16) || msg.DT_ENVIO}</span>
                            {isOut && <CheckCheck className="w-3.5 h-3.5" />}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {selectedConv.OBS_ATEND && (
                <div className="px-4 py-1.5 bg-amber-50 border-t border-amber-200 text-xs text-amber-800">
                  <strong>Nota interna do atendimento:</strong> {selectedConv.OBS_ATEND}
                </div>
              )}

              <form
                onSubmit={handleSendMessage}
                className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
              >
                <input
                  type="text"
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Digite sua mensagem comercial para o cliente..."
                  className="satiro-input flex-1"
                />
                <button type="submit" className="satiro-btn-primary px-5">
                  <Send className="w-4 h-4" /> Enviar
                </button>
              </form>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 p-8">
              <MessageSquare className="w-12 h-12 stroke-1 mb-2 text-slate-300" />
              <p className="text-sm font-medium">Selecione uma conversa ao lado para atender</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal Nova Conversa */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Iniciar Conversa WhatsApp</h2>
              <button onClick={() => setShowNewModal(false)} className="text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateConversation} className="p-6 space-y-4">
              <div>
                <label className="satiro-label">Nome do Contato *</label>
                <input
                  required
                  value={newForm.NOME_CONT}
                  onChange={(e) => setNewForm({ ...newForm, NOME_CONT: e.target.value })}
                  className="satiro-input"
                  placeholder="Ex: Marcos Compras"
                />
              </div>
              <div>
                <label className="satiro-label">Telefone / WhatsApp (com DDD) *</label>
                <input
                  required
                  value={newForm.TELEFONE}
                  onChange={(e) => setNewForm({ ...newForm, TELEFONE: e.target.value })}
                  className="satiro-input"
                  placeholder="Ex: 5511999998888"
                />
              </div>
              <div>
                <label className="satiro-label">Vincular Cliente (opcional)</label>
                <select
                  value={newForm.ID_CLIENTE}
                  onChange={(e) => setNewForm({ ...newForm, ID_CLIENTE: e.target.value })}
                  className="satiro-input"
                >
                  <option value="">Sem vínculo inicial</option>
                  {clients.map((c) => (
                    <option key={c.ID} value={c.ID}>
                      {c.NOME}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="satiro-btn-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="satiro-btn-primary">
                  Abrir Conversa
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Vincular Conversa */}
      {showLinkModal && selectedConv && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">
                Vincular Atendimento ao CRM
              </h2>
              <button onClick={() => setShowLinkModal(false)} className="text-slate-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSaveLink} className="p-6 space-y-4">
              <div>
                <label className="satiro-label">Cliente CRM</label>
                <select
                  value={linkForm.ID_CLIENTE}
                  onChange={(e) => setLinkForm({ ...linkForm, ID_CLIENTE: e.target.value })}
                  className="satiro-input"
                >
                  <option value="">Não vinculado</option>
                  {clients.map((c) => (
                    <option key={c.ID} value={c.ID}>
                      {c.NOME}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="satiro-label">Oportunidade Comercial</label>
                <select
                  value={linkForm.ID_OPORT}
                  onChange={(e) => setLinkForm({ ...linkForm, ID_OPORT: e.target.value })}
                  className="satiro-input"
                >
                  <option value="">Nenhuma oportunidade</option>
                  {opportunities.map((o) => (
                    <option key={o.ID} value={o.ID}>
                      {o.TITULO}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="satiro-label">Situação do Atendimento</label>
                <select
                  value={linkForm.SITUACAO}
                  onChange={(e) => setLinkForm({ ...linkForm, SITUACAO: e.target.value })}
                  className="satiro-input"
                >
                  <option value="EM_ATENDIMENTO">EM ATENDIMENTO</option>
                  <option value="AGUARDANDO">AGUARDANDO CLIENTE</option>
                  <option value="ENCERRADA">ENCERRADA</option>
                </select>
              </div>
              <div>
                <label className="satiro-label">Observações Internas</label>
                <input
                  value={linkForm.OBS_ATEND}
                  onChange={(e) => setLinkForm({ ...linkForm, OBS_ATEND: e.target.value })}
                  className="satiro-input"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="satiro-btn-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="satiro-btn-primary">
                  Salvar Vínculo
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

