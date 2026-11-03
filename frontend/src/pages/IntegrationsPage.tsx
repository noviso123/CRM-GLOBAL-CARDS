import React, { useEffect, useState } from 'react';
import {
  Plug,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  ShieldCheck,
  MessageSquare,
  Globe,
  Eye,
  EyeOff,
  Zap,
  Sparkles,
  Bot,
  Database,
  ArrowDownToLine,
  Layers,
  Terminal,
  Cpu,
  Send,
  Copy,
  Check,
  X,
  PhoneCall,
  Truck,
  Box,
} from 'lucide-react';
import { SupplierImportModal } from '../components/suppliers/SupplierImportModal';
import { apiRequest } from '../services/api';
import type { IntegrationStatusRecord } from '../types/crm';

export const IntegrationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'express' | 'mcp' | 'advanced' | 'suppliers'>('express');
  const [supplierModalOpen, setSupplierModalOpen] = useState(false);
  const [statuses, setStatuses] = useState<IntegrationStatusRecord[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [expressLoading, setExpressLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  // Estado do MCP
  const [mcpTools, setMcpTools] = useState<Array<{ name: string; description: string; category?: string; inputSchema?: any }>>([]);
  const [mcpResult, setMcpResult] = useState<any>(null);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [mcpCategory, setMcpCategory] = useState<string>('Todas');

  // Estado do WhatsApp & Meta
  const [waAccount, setWaAccount] = useState<any>(null);
  const [showTestWaModal, setShowTestWaModal] = useState(false);
  const [testPhone, setTestPhone] = useState('5511987654321');
  const [testMsg, setTestMsg] = useState('Global Cards: Olá! Teste de integração oficial com a Meta WhatsApp Cloud API realizado com sucesso.');
  const [testSending, setTestSending] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleFullSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await apiRequest<{
        status: string;
        message: string;
        inbound_from_bling: any;
        outbound_to_bling: any;
        cross_channel_whatsapp: any;
        total_records_processed: number;
      }>('/integrations/full-sync-omnidirectional', { method: 'POST' });

      setSyncResult(
        `🎉 Sincronização 100% Total Concluída (${res.total_records_processed} registros): Bling ➔ CRM (${res.inbound_from_bling?.products || 0} prod, ${res.inbound_from_bling?.contacts || 0} cli, ${res.inbound_from_bling?.orders || 0} ped) | CRM ➔ Bling (${res.outbound_to_bling?.products_exported || 0} prod, ${res.outbound_to_bling?.clients_exported || 0} cli, ${res.outbound_to_bling?.orders_exported || 0} ped) | WhatsApp (${res.cross_channel_whatsapp?.conversations_linked || 0} conversas vinculadas).`
      );
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro na sincronização bidirecional');
    } finally {
      setSyncing(false);
    }
  };

  const toggleSecret = (field: string) => {
    setShowSecrets((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const [blingForm, setBlingForm] = useState({
    client_id: '',
    client_secret: '',
    redirect_uri: 'http://127.0.0.1:8765/api/integrations/bling/oauth/callback',
    access_token: '',
    refresh_token: '',
  });

  const [waForm, setWaForm] = useState({
    phone_number_id: '',
    access_token: '',
    verify_token: 'globalcards_wa_verify',
  });

  const [metaForm, setMetaForm] = useState({
    app_id: '',
    app_secret: '',
    business_id: '',
  });

  const loadStatus = async () => {
    try {
      const [res, configs, mcpRes, waAcc] = await Promise.all([
        apiRequest<IntegrationStatusRecord[]>('/integrations/status'),
        apiRequest<{
          bling: typeof blingForm;
          whatsapp: typeof waForm;
          meta: typeof metaForm;
        }>('/integrations/configs'),
        apiRequest<{ tools: any[] }>('/integrations/mcp/tools').catch(() => ({ tools: [] })),
        apiRequest<any>('/whatsapp/status').catch(() => null),
      ]);
      setStatuses(res);
      if (configs.bling) setBlingForm((prev) => ({ ...prev, ...configs.bling }));
      if (configs.whatsapp) setWaForm((prev) => ({ ...prev, ...configs.whatsapp }));
      if (configs.meta) setMetaForm((prev) => ({ ...prev, ...configs.meta }));
      if (mcpRes.tools) setMcpTools(mcpRes.tools);
      if (waAcc) setWaAccount(waAcc);
    } catch {
      const res = await apiRequest<IntegrationStatusRecord[]>('/integrations/status');
      setStatuses(res);
    }
  };

  useEffect(() => {
    void loadStatus();
  }, []);

  const handleSaveBling = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiRequest('/integrations/bling/config', {
      method: 'POST',
      body: JSON.stringify(blingForm),
    });
    setSyncResult('Credenciais do Bling API v3 salvas com sucesso.');
    await loadStatus();
  };

  const handleTriggerSync = async (scopes: string[]) => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await apiRequest<{
        status: string;
        synced?: { products: number; contacts: number; orders: number };
        total_synced?: number;
      }>('/integrations/bling/sync', {
        method: 'POST',
        body: JSON.stringify({ scopes }),
      });
      const count =
        res.total_synced ??
        (res.synced ? res.synced.products + res.synced.contacts + res.synced.orders : 0);
      setSyncResult(
        `🎉 Sincronização concluída com sucesso (${res.status}): ${count} registros importados para as tabelas DBF locais.`
      );
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro na sincronização');
    } finally {
      setSyncing(false);
    }
  };

  const handleAutoImportAll = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await apiRequest<{ status: string; message: string; details: any }>(
        '/integrations/auto-import-all',
        { method: 'POST' }
      );
      setSyncResult(res.message);
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro na importação total.');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    const handleAuthMessage = (event: MessageEvent) => {
      if (event.data?.type === 'BLING_AUTH_SUCCESS') {
        setSyncResult(
          '🎉 Bling autorizado com sucesso via OAuth 2.0! Todos os dados estão sendo sincronizados automaticamente em segundo plano...'
        );
        void loadStatus();
        void handleAutoImportAll();
      }
      if (event.data?.type === 'META_AUTH_SUCCESS') {
        setSyncResult(
          '🎉 WhatsApp & Meta conectados com sucesso via Facebook Login for Business! Sua linha comercial oficial está ativa.'
        );
        void loadStatus();
      }
    };
    window.addEventListener('message', handleAuthMessage);
    return () => window.removeEventListener('message', handleAuthMessage);
  }, []);

  const handleOpenBlingPopup = async () => {
    try {
      const res = await apiRequest<{ authorize_url: string }>(
        '/integrations/bling/oauth/authorize-url'
      );
      const w = 640;
      const h = 760;
      const left = window.screen.width / 2 - w / 2;
      const top = window.screen.height / 2 - h / 2;
      window.open(
        res.authorize_url,
        'bling_oauth_popup',
        `width=${w},height=${h},top=${top},left=${left},status=no,resizable=yes`
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao abrir tela de autorização do Bling.');
    }
  };

  const handleOpenMetaPopup = async () => {
    try {
      const res = await apiRequest<{ authorize_url: string }>(
        '/whatsapp/oauth/authorize-url'
      );
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
      alert(err instanceof Error ? err.message : 'Erro ao abrir tela de autorização da Meta.');
    }
  };

  const handleFastConnectWhatsApp = async () => {
    setExpressLoading(true);
    try {
      const res = await apiRequest<{ message: string }>('/whatsapp/fast-connect', {
        method: 'POST',
        body: JSON.stringify({
          phone_number: '5511987654321',
          display_name: 'Global Cards Atendimento Oficial',
        }),
      });
      setSyncResult(res.message);
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro ao conectar WhatsApp da Meta');
    } finally {
      setExpressLoading(false);
    }
  };

  const handleSendTestWa = async (e: React.FormEvent) => {
    e.preventDefault();
    setTestSending(true);
    try {
      const res = await apiRequest<{ status: string }>('/whatsapp/test-send', {
        method: 'POST',
        body: JSON.stringify({ to_phone: testPhone, message: testMsg }),
      });
      setSyncResult(`✅ Mensagem de teste enviada com sucesso para ${testPhone}! Status: ${res.status}`);
      setShowTestWaModal(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Falha ao enviar mensagem de teste');
    } finally {
      setTestSending(false);
    }
  };

  const handleExpressSetup = async () => {
    setExpressLoading(true);
    try {
      const res = await apiRequest<{ status: string; message: string }>('/integrations/express-setup', {
        method: 'POST',
        body: JSON.stringify({
          client_id: blingForm.client_id || 'globalcards_bling_client',
          client_secret: blingForm.client_secret || 'globalcards_bling_secret_auto',
          phone_number_id: waForm.phone_number_id || '5511999998888',
          app_id: metaForm.app_id || 'globalcards_meta_app',
        }),
      });
      setSyncResult(res.message);
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro na configuração expressa.');
    } finally {
      setExpressLoading(false);
    }
  };

  const handleExecuteMcpTool = async (toolName: string, args: Record<string, any> = {}) => {
    setMcpLoading(true);
    try {
      const res = await apiRequest<any>('/integrations/mcp/execute', {
        method: 'POST',
        body: JSON.stringify({ tool: toolName, arguments: args }),
      });
      setMcpResult({ tool: toolName, response: res });
      await loadStatus();
    } catch (err) {
      setMcpResult({ tool: toolName, error: err instanceof Error ? err.message : 'Erro na execução MCP' });
    } finally {
      setMcpLoading(false);
    }
  };

  const handleSaveWa = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiRequest('/integrations/whatsapp/config', {
      method: 'POST',
      body: JSON.stringify(waForm),
    });
    setSyncResult('Configuração do WhatsApp Business Cloud API salva com sucesso.');
    await loadStatus();
  };

  const handleSaveMeta = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiRequest('/integrations/meta/config', {
      method: 'POST',
      body: JSON.stringify(metaForm),
    });
    setSyncResult('Configuração da Meta Graph API salva com sucesso.');
    await loadStatus();
  };

  const blingStatus = statuses.find((s) => s.PROVEDOR === 'BLING')?.SITUACAO || 'DESCONECTADO';
  const waStatus = statuses.find((s) => s.PROVEDOR === 'WHATSAPP')?.SITUACAO || 'DESCONECTADO';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Hub de Integrações Inteligentes & Bling MCP</h1>
        <p className="text-sm text-slate-500">
          Conexão em 1 clique sem formulários manuais: faça login e importe todos os clientes, produtos e pedidos para as tabelas DBF locais.
        </p>
      </div>

      {syncResult && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-900 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{syncResult}</span>
          </div>
          <button onClick={() => setSyncResult(null)} className="text-xs font-bold underline text-emerald-800">
            OK
          </button>
        </div>
      )}

      {/* Navegação por Abas Segmentadas */}
      <div className="bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/90 flex flex-wrap gap-1.5 shadow-2xs">
        <button
          type="button"
          onClick={() => setActiveTab('express')}
          className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
            activeTab === 'express'
              ? 'bg-[#053679] text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <Zap className="w-4 h-4 text-[#ED6706]" />
          1. Conexão Facilitada (Zero Digitação / Só Login)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('mcp')}
          className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
            activeTab === 'mcp'
              ? 'bg-[#053679] text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <Bot className="w-4 h-4 text-emerald-500" />
          2. Bling MCP Server & Automação com IA
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('advanced')}
          className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
            activeTab === 'advanced'
              ? 'bg-[#053679] text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <ShieldCheck className="w-4 h-4 text-slate-400" />
          3. Chaves & Configurações Técnicas (Avançado)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('suppliers')}
          className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
            activeTab === 'suppliers'
              ? 'bg-[#053679] text-white shadow-sm'
              : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200/70'
          }`}
        >
          <Truck className="w-4 h-4 text-[#ED6706]" />
          4. Fornecedores Gráficos (Atual / Zap / Futura / Padrão)
        </button>
      </div>

      {/* ABA 1: CONEXÃO FACILITADA EM 1 CLIQUE */}
      {activeTab === 'express' && (
        <div className="space-y-6">
          {/* Banner Principal com Chamada para Ação */}
          <div className="rounded-2xl bg-gradient-to-r from-[#031E44] via-[#053679] to-[#042A5F] p-7 text-white shadow-xl relative overflow-hidden border border-white/10">
            <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="space-y-2 max-w-2xl">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ED6706]/20 text-[#ED6706] text-xs font-extrabold uppercase tracking-wider border border-[#ED6706]/40">
                  <Sparkles className="w-3.5 h-3.5" /> Integração 100% Automática
                </span>
                <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                  Conecte sua conta do Bling e WhatsApp sem preencher dados
                </h2>
                <p className="text-xs sm:text-sm text-blue-100 leading-relaxed">
                  Não é necessário criar aplicativos nem copiar Client ID ou chaves secretas. Basta clicar no botão de login, autorizar o acesso à sua conta e o CRM GLOBAL CARDS baixará automaticamente todos os seus clientes, produtos com estoque e histórico de vendas para o banco de dados DBF.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full lg:w-auto shrink-0">
                <button
                  type="button"
                  onClick={handleOpenBlingPopup}
                  className="px-6 py-3.5 rounded-xl bg-[#ED6706] hover:bg-[#C24F04] text-white font-black text-sm shadow-lg hover:shadow-orange-500/30 transition-all flex items-center justify-center gap-2 active:scale-95"
                >
                  <ExternalLink className="w-4 h-4" />
                  Conectar com Bling
                </button>
                <button
                  type="button"
                  disabled={syncing}
                  onClick={handleFullSync}
                  className="px-5 py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-black text-sm shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2 active:scale-95 disabled:opacity-50"
                  title="Sincroniza 100% dos dados em ambos os sentidos (Bling, CRM e WhatsApp)"
                >
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? 'Sincronizando...' : '⚡ Sincronizar Tudo (100% Bidirecional)'}
                </button>
              </div>
            </div>
          </div>

          {/* Cards Grandes dos Provedores Conectados */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CARD 1: BLING ERP */}
            <div className="gc-card p-6 flex flex-col justify-between space-y-5">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 shadow-2xs font-extrabold text-base">
                      BL
                    </div>
                    <div>
                      <h3 className="text-base font-extrabold text-slate-900">Bling ERP v3</h3>
                      <p className="text-xs text-slate-500">API Oficial OAuth 2.0 Multi-Tenant</p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      blingStatus === 'CONECTADO'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}
                  >
                    {blingStatus === 'CONECTADO' ? '● CONECTADO' : '○ DESCONECTADO'}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  Importa automaticamente clientes (PJ e PF), produtos, categorias, tabela de preços, estoque e pedidos de venda para o banco de dados nativo DBF local.
                </p>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Modo de Conexão:</span>
                    <strong className="text-slate-900">Aplicativo Oficial Homologado</strong>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Fluxo de Autenticação:</span>
                    <span className="font-mono text-emerald-700 font-bold">OAuth 2.0 Zero-Input</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Armazenamento:</span>
                    <span className="font-mono text-slate-800">Criptografia Local Fernet</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={handleOpenBlingPopup}
                    className="gc-btn-primary w-full py-2.5 text-xs font-bold"
                  >
                    <ExternalLink className="w-3.5 h-3.5" /> Login no Bling
                  </button>
                  <button
                    type="button"
                    disabled={syncing}
                    onClick={handleAutoImportAll}
                    className="gc-btn-orange w-full py-2.5 text-xs font-bold"
                  >
                    <ArrowDownToLine className="w-3.5 h-3.5" /> Importar Tudo
                  </button>
                </div>
                <button
                  type="button"
                  disabled={expressLoading}
                  onClick={handleExpressSetup}
                  className="w-full py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                >
                  ⚡ Ativar Demonstração Local Imediata (Sem Conta Bling)
                </button>
              </div>
            </div>

            {/* CARD 2: WHATSAPP BUSINESS CLOUD & META */}
            <div className="gc-card p-6 flex flex-col justify-between space-y-5">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shadow-2xs font-extrabold text-base">
                      <MessageSquare className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-base font-extrabold text-slate-900">WhatsApp Business Cloud</h3>
                      <p className="text-xs text-slate-500">Meta Graph API v21.0 Oficial</p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      waStatus === 'CONECTADO'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}
                  >
                    {waStatus === 'CONECTADO' ? '● CONECTADO' : '○ DESCONECTADO'}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  Envio e recepção de mensagens comerciais em tempo real, disparo de templates HSM homologados (pedidos, faturas e PIX) com vinculação direta a clientes e pedidos.
                </p>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Linha Ativa Meta:</span>
                    <strong className="text-slate-900 font-mono">
                      {waAccount?.display_phone_number || waForm.phone_number_id || '+55 (11) 98765-4321'}
                    </strong>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>WABA ID:</span>
                    <span className="font-mono text-emerald-700 font-bold">
                      {waAccount?.waba_id || 'WABA-GLOBALCARDS-META'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Qualidade / Limite:</span>
                    <span className="font-mono text-teal-700 font-bold">TIER 1K / ALTA (VERDE)</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Webhook Meta:</span>
                    <span className="font-mono text-slate-700 text-[11px] truncate max-w-[190px]">
                      /api/whatsapp/webhook
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={handleOpenMetaPopup}
                    className="w-full py-2.5 rounded-lg bg-[#25D366] hover:bg-[#1EBE5D] text-white text-xs font-black shadow-sm transition flex items-center justify-center gap-2 active:scale-95"
                  >
                    <ExternalLink className="w-3.5 h-3.5" /> Login com Meta
                  </button>
                  <button
                    type="button"
                    disabled={expressLoading}
                    onClick={handleFastConnectWhatsApp}
                    className="gc-btn-orange w-full py-2.5 text-xs font-bold active:scale-95"
                  >
                    <Zap className="w-3.5 h-3.5" /> Conexão em 1-Clique
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowTestWaModal(true)}
                    className="flex-1 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition flex items-center justify-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5 text-slate-500" /> Testar Envio de Mensagem
                  </button>
                  <button
                    type="button"
                    onClick={() => copyToClipboard('http://127.0.0.1:8765/api/whatsapp/webhook', 'webhook_url')}
                    className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition flex items-center gap-1"
                    title="Copiar URL do Webhook da Meta"
                  >
                    {copiedKey === 'webhook_url' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span className="hidden sm:inline">Webhook</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ABA 2: BLING MCP SERVER & IA */}
      {activeTab === 'mcp' && (
        <div className="space-y-6">
          <div className="gc-card p-6 bg-slate-900 text-white space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-2xl bg-[#053679] border border-blue-400/40 text-sky-300">
                  <Cpu className="w-7 h-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-black tracking-tight text-white">Servidor Bling MCP Ativo</h2>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/40 text-[10px] font-bold">
                      Protocolo Oficial 2024-11-05
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">
                    Model Context Protocol (MCP) conectando Inteligência Artificial, ERP Bling e o Motor Nativo DBF.
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono text-sky-200 bg-white/10 px-3 py-1.5 rounded-lg border border-white/15">
                Endpoint: 127.0.0.1:8765/api/integrations/mcp
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed pt-2 border-t border-slate-800">
              O **Bling MCP** elimina a necessidade de exportar relatórios em planilhas ou preencher integrações manuais. Modelos de IA (como Gemini, Claude ou o copiloto interno do CRM) podem invocar ferramentas diretamente para consultar pedidos, validar estoques e disparar mensagens com governança e consentimento seguro.
            </p>
          </div>

          {/* Catálogo de Ferramentas MCP Prontas */}
          <div className="gc-card p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#053679]" /> Ferramentas MCP Disponíveis ({mcpTools.length})
                </h3>
                <p className="text-xs text-slate-500">
                  Execute ferramentas autônomas do protocolo MCP diretamente ou conecte agentes externos.
                </p>
              </div>

              {/* Filtro por Categoria */}
              <div className="flex flex-wrap gap-1 bg-slate-100 p-1 rounded-xl">
                {['Todas', 'Bling ERP', 'WhatsApp & Meta', 'Fornecedores Gráficos', 'CRM Comercial', 'BI & Métricas'].map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setMcpCategory(cat)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition ${
                      mcpCategory === cat
                        ? 'bg-[#053679] text-white shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(mcpCategory === 'Todas' ? mcpTools : mcpTools.filter((t) => t.category === mcpCategory)).map((t) => (
                <div key={t.name} className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/60 space-y-3 flex flex-col justify-between hover:border-sky-300 transition-colors">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="font-mono text-xs font-black text-[#053679] truncate">
                        {t.name}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-blue-100/70 text-[#053679] text-[10px] font-bold shrink-0">
                        {t.category || 'Geral'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                      {t.description}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={mcpLoading}
                    onClick={() => handleExecuteMcpTool(t.name, {})}
                    className="gc-btn-secondary w-full py-1.5 text-xs font-bold"
                  >
                    Testar Execução MCP
                  </button>
                </div>
              ))}
            </div>

            {/* Configuração MCP para Claude Desktop & Cursor */}
            <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-[#ED6706]" /> Conectar Claude Desktop, Cursor ou Agentes Externos
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Endpoint JSON-RPC 2.0 padrão ativo em: <code className="font-mono text-slate-800 font-bold">http://127.0.0.1:8765/api/integrations/mcp/rpc</code>
                </p>
              </div>
              <button
                type="button"
                onClick={() =>
                  copyToClipboard(
                    JSON.stringify(
                      {
                        mcpServers: {
                          'crm-globalcards': {
                            url: 'http://127.0.0.1:8765/api/integrations/mcp/rpc',
                          },
                        },
                      },
                      null,
                      2
                    ),
                    'mcp_config'
                  )
                }
                className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-xs font-bold text-slate-700 flex items-center gap-1.5 shrink-0"
              >
                {copiedKey === 'mcp_config' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                Copiar Configuração MCP
              </button>
            </div>

            {/* Terminal de Resposta da Execução MCP */}
            {mcpResult && (
              <div className="mt-5 p-4 rounded-xl bg-slate-950 text-emerald-400 font-mono text-xs space-y-2 border border-slate-800">
                <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-1.5">
                  <span className="flex items-center gap-1.5 font-bold">
                    <Terminal className="w-4 h-4 text-emerald-400" /> Output da Tool MCP: {mcpResult.tool}
                  </span>
                  <button onClick={() => setMcpResult(null)} className="hover:text-white">
                    Fechar
                  </button>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap max-h-60 leading-relaxed">
                  {JSON.stringify(mcpResult.response || mcpResult.error, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ABA 3: CHAVES E CONFIGURAÇÕES TÉCNICAS (AVANÇADO) */}
      {activeTab === 'advanced' && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <strong>Atenção Desenvolvedores:</strong> Esta aba é opcional e destinada apenas para inspeção manual ou personalização de credenciais de APIs próprias. Para uso normal, utilize a <strong>Aba 1 (Conexão Facilitada)</strong>.
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bling Manual */}
            <div className="gc-card p-6 space-y-4">
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Plug className="w-5 h-5 text-[#053679]" /> Credenciais Manuais Bling API v3
              </h3>
              <form onSubmit={handleSaveBling} className="space-y-3" autoComplete="off">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="satiro-label">Client ID (Bling Developer)</label>
                    <input
                      name="bling_dev_api_client_id"
                      autoComplete="new-password"
                      value={blingForm.client_id}
                      onChange={(e) => setBlingForm({ ...blingForm, client_id: e.target.value })}
                      className="satiro-input font-mono text-xs"
                      placeholder="Ex: c47b98a09f3e... (Portal Bling)"
                    />
                  </div>
                  <div>
                    <label className="satiro-label">Client Secret (Bling Developer)</label>
                    <div className="relative">
                      <input
                        name="bling_dev_api_client_secret"
                        autoComplete="new-password"
                        type={showSecrets.bling_secret ? 'text' : 'password'}
                        value={blingForm.client_secret}
                        onChange={(e) => setBlingForm({ ...blingForm, client_secret: e.target.value })}
                        className="satiro-input font-mono text-xs pr-9"
                        placeholder="••••••••••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => toggleSecret('bling_secret')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                        title={showSecrets.bling_secret ? 'Ocultar' : 'Visualizar'}
                      >
                        {showSecrets.bling_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="satiro-label">Redirect URI</label>
                  <input
                    value={blingForm.redirect_uri}
                    onChange={(e) => setBlingForm({ ...blingForm, redirect_uri: e.target.value })}
                    className="satiro-input font-mono text-xs"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="satiro-label">Access Token</label>
                    <div className="relative">
                      <input
                        type={showSecrets.bling_access ? 'text' : 'password'}
                        value={blingForm.access_token}
                        onChange={(e) => setBlingForm({ ...blingForm, access_token: e.target.value })}
                        className="satiro-input font-mono text-xs pr-9"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => toggleSecret('bling_access')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                      >
                        {showSecrets.bling_access ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="satiro-label">Refresh Token</label>
                    <div className="relative">
                      <input
                        type={showSecrets.bling_refresh ? 'text' : 'password'}
                        value={blingForm.refresh_token}
                        onChange={(e) => setBlingForm({ ...blingForm, refresh_token: e.target.value })}
                        className="satiro-input font-mono text-xs pr-9"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => toggleSecret('bling_refresh')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                      >
                        {showSecrets.bling_refresh ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                <button type="submit" className="gc-btn-primary">
                  Salvar Credenciais Bling
                </button>
              </form>
            </div>

            {/* WhatsApp Manual */}
            <div className="gc-card p-6 space-y-4">
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-teal-600" /> Credenciais Manuais WhatsApp & Meta
              </h3>
              <form onSubmit={handleSaveWa} className="space-y-3" autoComplete="off">
                <div>
                  <label className="satiro-label">Webhook Callback URL (Meta Developers)</label>
                  <div className="flex gap-2">
                    <input
                      readOnly
                      value="http://127.0.0.1:8765/api/whatsapp/webhook"
                      className="satiro-input font-mono text-xs bg-slate-100 flex-1"
                    />
                    <button
                      type="button"
                      onClick={() => copyToClipboard('http://127.0.0.1:8765/api/whatsapp/webhook', 'hook')}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-bold hover:bg-slate-50 flex items-center gap-1"
                    >
                      {copiedKey === 'hook' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="satiro-label">Webhook Verify Token</label>
                  <div className="relative">
                    <input
                      name="meta_wa_webhook_verify_token"
                      autoComplete="new-password"
                      type={showSecrets.wa_verify ? 'text' : 'password'}
                      value={waForm.verify_token}
                      onChange={(e) => setWaForm({ ...waForm, verify_token: e.target.value })}
                      className="satiro-input font-mono text-xs pr-16"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => toggleSecret('wa_verify')}
                        className="text-slate-400 hover:text-slate-600 p-1"
                      >
                        {showSecrets.wa_verify ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(waForm.verify_token, 'verify_tok')}
                        className="text-slate-400 hover:text-slate-600 p-1"
                      >
                        {copiedKey === 'verify_tok' ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="satiro-label">Phone Number ID (Meta Graph)</label>
                  <input
                    name="meta_wa_phone_number_identifier"
                    autoComplete="new-password"
                    value={waForm.phone_number_id}
                    onChange={(e) => setWaForm({ ...waForm, phone_number_id: e.target.value })}
                    className="satiro-input font-mono text-xs"
                    placeholder="5511999998888"
                  />
                </div>
                <div>
                  <label className="satiro-label">Permanent Access Token (System User Meta)</label>
                  <div className="relative">
                    <input
                      name="meta_wa_permanent_token_system"
                      autoComplete="new-password"
                      type={showSecrets.wa_access ? 'text' : 'password'}
                      value={waForm.access_token}
                      onChange={(e) => setWaForm({ ...waForm, access_token: e.target.value })}
                      className="satiro-input font-mono text-xs pr-9"
                      placeholder="••••••••••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecret('wa_access')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                    >
                      {showSecrets.wa_access ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <button type="submit" className="gc-btn-primary">
                  Salvar Credenciais WhatsApp
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ABA 4: FORNECEDORES GRÁFICOS HOMOLOGADOS */}
      {activeTab === 'suppliers' && (
        <div className="space-y-6">
          {/* Banner Principal de Fornecedores */}
          <div className="rounded-2xl bg-gradient-to-r from-[#03224C] via-[#053679] to-[#0A4B9E] p-7 text-white shadow-xl relative overflow-hidden border border-white/10">
            <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
              <div className="space-y-2 max-w-2xl">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange-500 text-white text-xs font-extrabold uppercase tracking-wider shadow-xs">
                  <Truck className="w-3.5 h-3.5" /> Fornecedores Gráficos Parceiros
                </span>
                <h3 className="text-2xl font-black tracking-tight text-white">
                  Importação Facilitada de Catálogos & Produtos
                </h3>
                <p className="text-xs text-blue-100/90 leading-relaxed">
                  Conecte-se aos maiores fabricantes e revendas gráficas do Brasil. Pesquise no catálogo integrado ou cole o link do produto da <strong>Atual Card</strong>, <strong>Zap Gráfica</strong>, <strong>FuturaIM</strong> ou <strong>Padrão Color</strong>. O CRM extrai fotos, fichas técnicas e custos, cadastra no DBF local e sincroniza 100% no <strong>Bling ERP v3</strong>.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSupplierModalOpen(true)}
                className="shrink-0 px-6 py-3.5 rounded-xl bg-gradient-to-r from-orange-500 to-[#E86014] hover:from-orange-600 hover:to-orange-700 text-white font-extrabold text-sm shadow-lg shadow-orange-500/30 flex items-center gap-2.5 transition-all hover:scale-[1.03]"
              >
                <Sparkles className="w-5 h-5" />
                Abrir Central de Importação (4 Gráficas)
              </button>
            </div>
          </div>

          {/* Cards dos 4 Fabricantes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* 1. ATUAL CARD */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-orange-600 text-white flex items-center justify-center font-black text-sm shadow-xs">
                      AC
                    </div>
                    <div>
                      <h4 className="font-extrabold text-slate-900 text-sm">Atual Card</h4>
                      <span className="text-[11px] text-slate-400 font-mono">atualcard.com.br</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Homologado
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                  Referência nacional em cartões de visita, crachás plásticos em PVC 0.76mm (padrão ISO), cordões personalizados e impressos de alta tiragem.
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {['Crachás PVC 0.76mm', 'Cordões Sublimáticos', 'Cartões Couchê 300g', 'Pastas Executivas'].map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] font-semibold text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <a
                  href="https://www.atualcard.com.br"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-slate-500 hover:text-slate-800 font-semibold inline-flex items-center gap-1"
                >
                  Visitar Site Oficial <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
                <button
                  type="button"
                  onClick={() => setSupplierModalOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 font-bold text-xs"
                >
                  Importar Produtos
                </button>
              </div>
            </div>

            {/* 2. ZAP GRÁFICA */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-sm shadow-xs">
                      ZG
                    </div>
                    <div>
                      <h4 className="font-extrabold text-slate-900 text-sm">Zap Gráfica</h4>
                      <span className="text-[11px] text-slate-400 font-mono">zapgrafica.com.br</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Homologado
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                  A maior gráfica expressa da América Latina para revendedores. Produção em escala de crachás com chip RFID/Mifare, credenciais, banners e brindes.
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {['Crachás com Chip RFID', 'Credenciais 9x13cm', 'Cordões com Trava', 'Banners em Lona'].map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] font-semibold text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <a
                  href="https://www.zapgrafica.com.br"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-slate-500 hover:text-slate-800 font-semibold inline-flex items-center gap-1"
                >
                  Visitar Site Oficial <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
                <button
                  type="button"
                  onClick={() => setSupplierModalOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-bold text-xs"
                >
                  Importar Produtos
                </button>
              </div>
            </div>

            {/* 3. FUTURAIM */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-black text-sm shadow-xs">
                      FM
                    </div>
                    <div>
                      <h4 className="font-extrabold text-slate-900 text-sm">FuturaIM</h4>
                      <span className="text-[11px] text-slate-400 font-mono">futuraim.com.br</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Homologado
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                  Gráfica online completa com acabamentos especiais, roller clips resinados, porta crachás rígidos, adesivos vinil e brindes corporativos.
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {['Roller Clip Resinado', 'Porta Crachá Rígido', 'Adesivos Vinil', 'Panfletos Couchê'].map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] font-semibold text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <a
                  href="https://www.futuraim.com.br"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-slate-500 hover:text-slate-800 font-semibold inline-flex items-center gap-1"
                >
                  Visitar Site Oficial <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
                <button
                  type="button"
                  onClick={() => setSupplierModalOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-bold text-xs"
                >
                  Importar Produtos
                </button>
              </div>
            </div>

            {/* 4. PADRÃO COLOR */}
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-amber-600 text-white flex items-center justify-center font-black text-sm shadow-xs">
                      PC
                    </div>
                    <div>
                      <h4 className="font-extrabold text-slate-900 text-sm">Padrão Color</h4>
                      <span className="text-[11px] text-slate-400 font-mono">padraocolor.com.br</span>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Homologado
                  </span>
                </div>
                <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                  Gráfica especializada em revenda para agências e profissionais gráficos, envelopes timbrados, pastas com bolsa e cartões de fidelidade.
                </p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {['Envelopes Ofício', 'Cartões Fidelidade', 'Pastas com Bolsa', 'Impressão Offset'].map((tag) => (
                    <span key={tag} className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] font-semibold text-slate-600">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <a
                  href="https://www.padraocolor.com.br"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-slate-500 hover:text-slate-800 font-semibold inline-flex items-center gap-1"
                >
                  Visitar Site Oficial <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
                <button
                  type="button"
                  onClick={() => setSupplierModalOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 font-bold text-xs"
                >
                  Importar Produtos
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Central de Importação dos 4 Fornecedores Gráficos */}
      <SupplierImportModal
        isOpen={supplierModalOpen}
        onClose={() => setSupplierModalOpen(false)}
        onImportSuccess={() => loadStatus()}
      />

      {/* Modal de Teste de Envio WhatsApp */}
      {showTestWaModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center">
                  <Send className="w-4 h-4" />
                </div>
                <h3 className="text-base font-extrabold text-slate-900">Testar Envio via Meta API</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowTestWaModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSendTestWa} className="p-6 space-y-4">
              <div>
                <label className="satiro-label">Telefone de Destino (com DDD e DDI 55) *</label>
                <input
                  required
                  value={testPhone}
                  onChange={(e) => setTestPhone(e.target.value)}
                  placeholder="Ex: 5511999998888"
                  className="satiro-input font-mono text-sm"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Recomendado usar o número do seu celular para validar o recebimento.
                </p>
              </div>

              <div>
                <label className="satiro-label">Mensagem de Teste *</label>
                <textarea
                  required
                  rows={3}
                  value={testMsg}
                  onChange={(e) => setTestMsg(e.target.value)}
                  className="satiro-input text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowTestWaModal(false)}
                  className="gc-btn-secondary py-2 text-xs"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={testSending}
                  className="gc-btn-primary py-2 text-xs flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  {testSending ? 'Disparando...' : 'Disparar Teste'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
