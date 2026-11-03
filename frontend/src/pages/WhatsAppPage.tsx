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
  Zap,
  ExternalLink,
  FileText,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  QrCode,
  RefreshCw,
  Sliders,
  Check,
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

  // Estado de conexão WhatsApp / Meta
  const [waStatus, setWaStatus] = useState<any>(null);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [connectLoading, setConnectLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Estado dos templates oficiais da Meta
  const [templates, setTemplates] = useState<any[]>([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [templateParams, setTemplateParams] = useState<string[]>([]);
  const [sendingTemplate, setSendingTemplate] = useState(false);

  // Modais de conversa e vínculo
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

  const loadStatus = async () => {
    try {
      const s = await apiRequest<any>('/whatsapp/status');
      setWaStatus(s);
    } catch {
      setWaStatus(null);
    }
  };

  const loadTemplates = async () => {
    try {
      const list = await apiRequest<any[]>('/whatsapp/templates');
      setTemplates(list);
      if (list.length > 0 && !selectedTemplate) {
        setSelectedTemplate(list[0]);
        setTemplateParams(new Array(list[0].parameters.length).fill(''));
      }
    } catch {
      setTemplates([]);
    }
  };

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
    void loadConversations();
    void loadStatus();
  }, [statusFilter]);

  // Escuta confirmação do popup de login da Meta
  useEffect(() => {
    const handleAuthMessage = (event: MessageEvent) => {
      if (event.data?.type === 'META_AUTH_SUCCESS') {
        setToastMessage('🎉 WhatsApp & Meta conectados com sucesso via Facebook Login!');
        setShowConnectModal(false);
        void loadStatus();
      }
    };
    window.addEventListener('message', handleAuthMessage);
    return () => window.removeEventListener('message', handleAuthMessage);
  }, []);

  const handleOpenMetaPopup = async () => {
    try {
      const res = await apiRequest<{ authorize_url: string }>('/whatsapp/oauth/authorize-url');
      const w = 680;
      const h = 780;
      const left = window.screen.width / 2 - w / 2;
      const top = window.screen.height / 2 - h / 2;
      window.open(
        res.authorize_url,
        'meta_oauth_popup',
        `width=${w},height=${h},top=${top},left=${left},status=no,resizable=yes`
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao abrir autorização da Meta');
    }
  };

  const handleFastConnect = async () => {
    setConnectLoading(true);
    try {
      const res = await apiRequest<{ message: string }>('/whatsapp/fast-connect', {
        method: 'POST',
        body: JSON.stringify({
          phone_number: '5511987654321',
          display_name: 'Global Cards Atendimento Oficial',
        }),
      });
      setToastMessage(res.message);
      setShowConnectModal(false);
      await loadStatus();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao conectar');
    } finally {
      setConnectLoading(false);
    }
  };

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

  const handleSendTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedConv || !selectedTemplate) return;
    setSendingTemplate(true);
    try {
      await apiRequest(`/whatsapp/conversations/${selectedConv.ID}/send-template`, {
        method: 'POST',
        body: JSON.stringify({
          template_name: selectedTemplate.name,
          parameters: templateParams,
        }),
      });
      setShowTemplateModal(false);
      setToastMessage(`Template "${selectedTemplate.label}" enviado com sucesso!`);
      await selectConversation(selectedConv);
      await loadConversations();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao enviar template');
    } finally {
      setSendingTemplate(false);
    }
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

  const isConnected = Boolean(waStatus?.is_connected);

  return (
    <div className="space-y-4">
      {/* Toast de Confirmação */}
      {toastMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-900 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span className="font-medium">{toastMessage}</span>
          </div>
          <button
            onClick={() => setToastMessage(null)}
            className="text-xs font-bold underline text-emerald-800"
          >
            Fechar
          </button>
        </div>
      )}

      {/* Barra de Status e Conexão Rápida com a Meta */}
      <div className={`p-4 rounded-2xl border transition-all ${
        isConnected
          ? 'bg-gradient-to-r from-emerald-900/10 via-white to-teal-50/40 border-emerald-200'
          : 'bg-gradient-to-r from-amber-50 via-white to-orange-50 border-amber-200'
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold shrink-0 ${
              isConnected
                ? 'bg-[#25D366] text-white shadow-sm'
                : 'bg-amber-100 text-amber-700'
            }`}>
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-extrabold text-slate-900">
                  {isConnected
                    ? `WhatsApp Meta Conectado: ${waStatus.display_phone_number || '+55 (11) 98765-4321'}`
                    : 'WhatsApp Desconectado — Conecte sua Conta Meta Oficial'}
                </h2>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                  isConnected
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                    : 'bg-amber-50 text-amber-700 border-amber-300'
                }`}>
                  {isConnected ? '● META CLOUD API ATIVA' : '○ DESCONECTADO'}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {isConnected
                  ? `Linha: ${waStatus.verified_name || 'Global Cards Atendimento'} | WABA ID: ${waStatus.waba_id || 'Oficial'} | Qualidade: ALTA`
                  : 'Integração facilitada em 1 clique: conecte sua conta para enviar orçamentos, pedidos e mensagens automáticas.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {isConnected ? (
              <>
                <button
                  type="button"
                  onClick={() => setShowConnectModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold transition flex items-center gap-1.5"
                >
                  <Sliders className="w-3.5 h-3.5 text-slate-400" /> Detalhes da Linha
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={handleOpenMetaPopup}
                  className="px-4 py-2 rounded-xl bg-[#25D366] hover:bg-[#1EBE5D] text-white font-black text-xs shadow-sm transition flex items-center gap-1.5 active:scale-95"
                >
                  <ExternalLink className="w-3.5 h-3.5" /> Login com Meta
                </button>
                <button
                  type="button"
                  disabled={connectLoading}
                  onClick={handleFastConnect}
                  className="gc-btn-orange px-4 py-2 text-xs font-bold active:scale-95 flex items-center gap-1.5"
                >
                  <Zap className="w-3.5 h-3.5" /> Conexão em 1-Clique
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Cabeçalho da Central */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Atendimento & WhatsApp Comercial</h1>
          <p className="text-sm text-slate-500">
            Central de conversas integrada com vinculação direta a clientes, contatos e oportunidades.
          </p>
        </div>
        <button onClick={() => setShowNewModal(true)} className="gc-btn-primary">
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
                      ? 'bg-[#053679] text-white shadow-xs'
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
                      ? 'bg-emerald-50/90 border-l-4 border-l-[#053679]'
                      : 'hover:bg-white'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-slate-200 text-[#053679] font-bold text-sm flex items-center justify-center shrink-0">
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
                        <span className="px-1.5 py-0.5 rounded-full bg-[#ED6706] text-white text-[10px] font-bold">
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
                  <div className="w-10 h-10 rounded-full bg-[#053679] text-white font-bold flex items-center justify-center">
                    {selectedConv.NOME_CONT.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      {selectedConv.NOME_CONT}
                      <span className="text-[10px] font-mono font-normal text-slate-400">
                        ({selectedConv.TELEFONE})
                      </span>
                    </h2>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      {selectedConv.CLIENTE_NOME ? (
                        <span className="flex items-center gap-1 text-slate-700">
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          {selectedConv.CLIENTE_NOME}
                        </span>
                      ) : (
                        <span className="text-amber-600">Não vinculado a cliente</span>
                      )}
                      {selectedConv.OPORTUNIDADE_TITULO && (
                        <span className="flex items-center gap-1 text-slate-700">
                          <Target className="w-3.5 h-3.5 text-emerald-500" />
                          {selectedConv.OPORTUNIDADE_TITULO}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={openLinkModal}
                    className="gc-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
                  >
                    <LinkIcon className="w-3.5 h-3.5" /> Vincular ao CRM
                  </button>
                </div>
              </div>

              {/* Histórico de Mensagens */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400">
                    <MessageSquare className="w-10 h-10 stroke-1 mb-2 text-slate-300" />
                    <p className="text-xs">Nenhuma mensagem nesta conversa ainda.</p>
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isOut = msg.DIRECAO === 'SAIDA';
                    const isTemplate = msg.TIPO_MSG === 'TEMPLATE';
                    return (
                      <div
                        key={msg.ID}
                        className={`flex ${isOut ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[75%] rounded-2xl p-3 text-xs shadow-2xs ${
                            isOut
                              ? isTemplate
                                ? 'bg-teal-700 text-white rounded-br-xs'
                                : 'bg-[#053679] text-white rounded-br-xs'
                              : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs'
                          }`}
                        >
                          {isTemplate && (
                            <span className="inline-block px-1.5 py-0.5 rounded bg-white/20 text-[10px] font-bold uppercase tracking-wider mb-1">
                              Template Oficial Meta
                            </span>
                          )}
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.CONTEUDO}</p>
                          <div
                            className={`flex items-center justify-end gap-1 mt-1 text-[10px] ${
                              isOut ? 'text-blue-100' : 'text-slate-400'
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

              {/* Barra de Envio com Botão de Templates Meta */}
              <form
                onSubmit={handleSendMessage}
                className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
              >
                <button
                  type="button"
                  onClick={() => {
                    void loadTemplates();
                    setShowTemplateModal(true);
                  }}
                  className="px-3 py-2 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 font-bold text-xs border border-teal-200 transition flex items-center gap-1.5 shrink-0"
                  title="Disparar Template Oficial HSM (Meta)"
                >
                  <FileText className="w-4 h-4 text-teal-600" />
                  <span className="hidden sm:inline">Templates Meta</span>
                </button>

                <input
                  type="text"
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Digite sua mensagem comercial para o cliente..."
                  className="satiro-input flex-1 text-xs"
                />

                <button type="submit" className="gc-btn-primary px-5 py-2 text-xs flex items-center gap-1.5">
                  <Send className="w-3.5 h-3.5" /> Enviar
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

      {/* Modal Conexão Facilitada WhatsApp & Meta */}
      {showConnectModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <h3 className="text-base font-extrabold text-slate-900">
                  Conectar WhatsApp Oficial com a Meta
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowConnectModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Status Atual:</span>
                  <strong className={isConnected ? 'text-emerald-700 font-bold' : 'text-amber-700'}>
                    {isConnected ? '● CONECTADO' : '○ DESCONECTADO'}
                  </strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Linha Configurada:</span>
                  <span className="font-mono text-slate-800">
                    {waStatus?.display_phone_number || '+55 (11) 98765-4321'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">WABA ID:</span>
                  <span className="font-mono text-slate-800">{waStatus?.waba_id || 'Oficial Meta'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Webhook Meta:</span>
                  <span className="font-mono text-slate-800 text-[11px]">
                    {waStatus?.webhook_url || '/api/whatsapp/webhook'}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handleOpenMetaPopup}
                  className="w-full py-3 rounded-xl bg-[#25D366] hover:bg-[#1EBE5D] text-white font-black text-sm shadow-md transition flex items-center justify-center gap-2 active:scale-95"
                >
                  <ExternalLink className="w-4 h-4" />
                  Conectar com Meta (Facebook Login for Business)
                </button>

                <button
                  type="button"
                  disabled={connectLoading}
                  onClick={handleFastConnect}
                  className="gc-btn-orange w-full py-3 text-sm font-bold flex items-center justify-center gap-2 active:scale-95"
                >
                  <Zap className="w-4 h-4" />
                  ⚡ Conexão Rápida em 1-Clique (Linha GlobalCards)
                </button>
              </div>

              <p className="text-[11px] text-slate-400 text-center leading-relaxed">
                A conexão direta estabelece comunicação homologada com a Meta Graph API, garantindo alta entregabilidade e conformidade com os termos de serviço do WhatsApp Business.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal Disparo de Templates Oficiais Meta */}
      {showTemplateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-teal-50/70">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    Templates Oficiais da Meta (HSM)
                  </h3>
                  <p className="text-[11px] text-slate-500">Notificações comerciais pré-aprovadas</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowTemplateModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSendTemplate} className="p-6 space-y-4">
              <div>
                <label className="satiro-label">Selecione o Modelo de Mensagem *</label>
                <select
                  className="satiro-input text-xs"
                  value={selectedTemplate?.name || ''}
                  onChange={(e) => {
                    const tmpl = templates.find((t) => t.name === e.target.value);
                    if (tmpl) {
                      setSelectedTemplate(tmpl);
                      setTemplateParams(new Array(tmpl.parameters.length).fill(''));
                    }
                  }}
                >
                  {templates.map((t) => (
                    <option key={t.name} value={t.name}>
                      {t.label} ({t.category})
                    </option>
                  ))}
                </select>
              </div>

              {selectedTemplate && (
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
                  <p className="text-slate-500 font-medium">{selectedTemplate.description}</p>
                  <p className="p-2.5 rounded-lg bg-white border border-slate-200 font-mono text-[11px] text-slate-800">
                    {selectedTemplate.example}
                  </p>
                </div>
              )}

              {selectedTemplate && selectedTemplate.parameters.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Parâmetros do Template
                  </h4>
                  {selectedTemplate.parameters.map((paramName: string, idx: number) => (
                    <div key={idx}>
                      <label className="satiro-label">{paramName} *</label>
                      <input
                        required
                        value={templateParams[idx] || ''}
                        onChange={(e) => {
                          const copy = [...templateParams];
                          copy[idx] = e.target.value;
                          setTemplateParams(copy);
                        }}
                        className="satiro-input text-xs"
                        placeholder={`Preencha ${paramName}`}
                      />
                    </div>
                  ))}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowTemplateModal(false)}
                  className="gc-btn-secondary py-2 text-xs"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={sendingTemplate}
                  className="gc-btn-primary py-2 text-xs flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  {sendingTemplate ? 'Disparando...' : 'Disparar Template Oficial'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Nova Conversa */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl overflow-hidden border border-slate-200">
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
                  className="satiro-input text-xs"
                  placeholder="Ex: Marcos Compras"
                />
              </div>
              <div>
                <label className="satiro-label">Telefone / WhatsApp (com DDD) *</label>
                <input
                  required
                  value={newForm.TELEFONE}
                  onChange={(e) => setNewForm({ ...newForm, TELEFONE: e.target.value })}
                  className="satiro-input text-xs font-mono"
                  placeholder="Ex: 5511999998888"
                />
              </div>
              <div>
                <label className="satiro-label">Vincular Cliente (opcional)</label>
                <select
                  value={newForm.ID_CLIENTE}
                  onChange={(e) => setNewForm({ ...newForm, ID_CLIENTE: e.target.value })}
                  className="satiro-input text-xs"
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
                  className="gc-btn-secondary text-xs py-2"
                >
                  Cancelar
                </button>
                <button type="submit" className="gc-btn-primary text-xs py-2">
                  Abrir Conversa
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Vincular Conversa */}
      {showLinkModal && selectedConv && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full shadow-2xl overflow-hidden border border-slate-200">
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
                  className="satiro-input text-xs"
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
                  className="satiro-input text-xs"
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
                  className="satiro-input text-xs"
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
                  className="satiro-input text-xs"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="gc-btn-secondary text-xs py-2"
                >
                  Cancelar
                </button>
                <button type="submit" className="gc-btn-primary text-xs py-2">
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
