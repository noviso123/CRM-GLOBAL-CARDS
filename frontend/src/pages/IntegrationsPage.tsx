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
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type { IntegrationStatusRecord } from '../types/crm';

export const IntegrationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'express' | 'mcp' | 'advanced'>('express');
  const [statuses, setStatuses] = useState<IntegrationStatusRecord[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [expressLoading, setExpressLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  // Estado do MCP
  const [mcpTools, setMcpTools] = useState<Array<{ name: string; description: string; inputSchema?: any }>>([]);
  const [mcpResult, setMcpResult] = useState<any>(null);
  const [mcpLoading, setMcpLoading] = useState(false);

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
      const [res, configs, mcpRes] = await Promise.all([
        apiRequest<IntegrationStatusRecord[]>('/integrations/status'),
        apiRequest<{
          bling: typeof blingForm;
          whatsapp: typeof waForm;
          meta: typeof metaForm;
        }>('/integrations/configs'),
        apiRequest<{ tools: any[] }>('/integrations/mcp/tools').catch(() => ({ tools: [] })),
      ]);
      setStatuses(res);
      if (configs.bling) setBlingForm((prev) => ({ ...prev, ...configs.bling }));
      if (configs.whatsapp) setWaForm((prev) => ({ ...prev, ...configs.whatsapp }));
      if (configs.meta) setMetaForm((prev) => ({ ...prev, ...configs.meta }));
      if (mcpRes.tools) setMcpTools(mcpRes.tools);
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
                  Conectar com Bling (Login Direto)
                </button>
                <button
                  type="button"
                  disabled={syncing}
                  onClick={handleAutoImportAll}
                  className="px-5 py-3.5 rounded-xl bg-white/15 hover:bg-white/25 text-white font-bold text-sm border border-white/25 backdrop-blur-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <ArrowDownToLine className={`w-4 h-4 ${syncing ? 'animate-bounce' : ''}`} />
                  {syncing ? 'Baixando Dados...' : 'Importar Tudo do Bling Agora'}
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

            {/* CARD 2: WHATSAPP BUSINESS CLOUD */}
            <div className="gc-card p-6 flex flex-col justify-between space-y-5">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shadow-2xs font-extrabold text-base">
                      <MessageSquare className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-base font-extrabold text-slate-900">WhatsApp Business Cloud</h3>
                      <p className="text-xs text-slate-500">Meta Graph API Oficial</p>
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
                  Envio e recepção de mensagens comerciais diretamente pelo CRM, com vinculação imediata a clientes, contatos e oportunidades comerciais no funil de vendas.
                </p>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Modo de Conexão:</span>
                    <strong className="text-slate-900">Embedded Signup / Facebook Login</strong>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Disparo e Webhook:</span>
                    <span className="font-mono text-teal-700 font-bold">100% Automatizado</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Registro no DBF:</span>
                    <span className="font-mono text-slate-800">CONVERS.DBF & MENSAGEN.DBF</span>
                  </div>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleExpressSetup}
                  className="w-full py-2.5 rounded-lg bg-[#25D366] hover:bg-[#1EBE5D] text-white text-xs font-black shadow-sm transition flex items-center justify-center gap-2"
                >
                  <MessageSquare className="w-4 h-4" /> Conectar WhatsApp (Login com Meta)
                </button>
                <button
                  type="button"
                  disabled={expressLoading}
                  onClick={handleExpressSetup}
                  className="w-full py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                >
                  ⚡ Ativar Linha Comercial Global Cards
                </button>
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
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#053679]" /> Ferramentas MCP Disponíveis ({mcpTools.length})
                </h3>
                <p className="text-xs text-slate-500">
                  Clique em &ldquo;Testar Ferramenta&rdquo; para executar a tool do protocolo em tempo real.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mcpTools.map((t) => (
                <div key={t.name} className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/60 space-y-3 flex flex-col justify-between hover:border-sky-300 transition-colors">
                  <div>
                    <span className="font-mono text-xs font-black text-[#053679] block">
                      {t.name}
                    </span>
                    <p className="text-xs text-slate-600 mt-1 line-clamp-3 leading-relaxed">
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
              <form onSubmit={handleSaveBling} className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="satiro-label">Client ID</label>
                    <input
                      value={blingForm.client_id}
                      onChange={(e) => setBlingForm({ ...blingForm, client_id: e.target.value })}
                      className="satiro-input font-mono text-xs"
                      placeholder="globalcards_bling_client"
                    />
                  </div>
                  <div>
                    <label className="satiro-label">Client Secret</label>
                    <div className="relative">
                      <input
                        type={showSecrets.bling_secret ? 'text' : 'password'}
                        value={blingForm.client_secret}
                        onChange={(e) => setBlingForm({ ...blingForm, client_secret: e.target.value })}
                        className="satiro-input font-mono text-xs pr-9"
                        placeholder="••••••••"
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
              <form onSubmit={handleSaveWa} className="space-y-3">
                <div>
                  <label className="satiro-label">Phone Number ID</label>
                  <input
                    value={waForm.phone_number_id}
                    onChange={(e) => setWaForm({ ...waForm, phone_number_id: e.target.value })}
                    className="satiro-input font-mono text-xs"
                    placeholder="5511999998888"
                  />
                </div>
                <div>
                  <label className="satiro-label">Permanent Access Token</label>
                  <div className="relative">
                    <input
                      type={showSecrets.wa_access ? 'text' : 'password'}
                      value={waForm.access_token}
                      onChange={(e) => setWaForm({ ...waForm, access_token: e.target.value })}
                      className="satiro-input font-mono text-xs pr-9"
                      placeholder="••••••••"
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
    </div>
  );
};
