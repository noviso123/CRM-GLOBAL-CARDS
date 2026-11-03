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
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type { IntegrationStatusRecord } from '../types/crm';

export const IntegrationsPage: React.FC = () => {
  const [statuses, setStatuses] = useState<IntegrationStatusRecord[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [expressLoading, setExpressLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const toggleSecret = (field: string) => {
    setShowSecrets((prev) => ({ ...prev, [field]: !prev[field] }));
  };
  const [blingForm, setBlingForm] = useState({
    client_id: '',
    client_secret: '',
    redirect_uri: 'http://127.0.0.1:8000/api/integrations/bling/oauth/callback',
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
      const [res, configs] = await Promise.all([
        apiRequest<IntegrationStatusRecord[]>('/integrations/status'),
        apiRequest<{
          bling: typeof blingForm;
          whatsapp: typeof waForm;
          meta: typeof metaForm;
        }>('/integrations/configs'),
      ]);
      setStatuses(res);
      if (configs.bling) setBlingForm((prev) => ({ ...prev, ...configs.bling }));
      if (configs.whatsapp) setWaForm((prev) => ({ ...prev, ...configs.whatsapp }));
      if (configs.meta) setMetaForm((prev) => ({ ...prev, ...configs.meta }));
    } catch {
      const res = await apiRequest<IntegrationStatusRecord[]>('/integrations/status');
      setStatuses(res);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleSaveBling = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiRequest('/integrations/bling/config', {
      method: 'POST',
      body: JSON.stringify(blingForm),
    });
    setSyncResult('Credenciais do Bling API v3 salvas e criptografadas localmente (Fernet).');
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
        errors?: string[];
      }>('/integrations/bling/sync', {
        method: 'POST',
        body: JSON.stringify({ scopes }),
      });
      const count =
        res.total_synced ??
        (res.synced ? res.synced.products + res.synced.contacts + res.synced.orders : 0);
      setSyncResult(
        `Sincronização concluída (${res.status}): ${count} registros processados.`
      );
      await loadStatus();
    } catch (err) {
      setSyncResult(err instanceof Error ? err.message : 'Erro na sincronização');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    const handleAuthMessage = (event: MessageEvent) => {
      if (event.data?.type === 'BLING_AUTH_SUCCESS') {
        setSyncResult('🎉 Bling autorizado com sucesso via OAuth 2.0! Executando sincronização inicial automática...');
        void loadStatus();
        void handleTriggerSync(['all']);
      }
    };
    window.addEventListener('message', handleAuthMessage);
    return () => window.removeEventListener('message', handleAuthMessage);
  }, []);

  const handleOpenBlingPopup = async () => {
    try {
      if (!blingForm.client_id) {
        alert('Por favor, informe seu Client ID do Bling no campo abaixo para conectar.');
        return;
      }
      const res = await apiRequest<{ authorize_url: string }>(
        '/integrations/bling/oauth/authorize-url'
      );
      const w = 620;
      const h = 740;
      const left = window.screen.width / 2 - w / 2;
      const top = window.screen.height / 2 - h / 2;
      window.open(
        res.authorize_url,
        'bling_oauth_popup',
        `width=${w},height=${h},top=${top},left=${left},status=no,resizable=yes`
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Configure o Client ID do Bling primeiro.');
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

  const handleOpenBlingOAuth = async () => {
    try {
      const res = await apiRequest<{ authorize_url: string }>(
        '/integrations/bling/oauth/authorize-url'
      );
      window.open(res.authorize_url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Salve o Client ID do Bling primeiro.');
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Hub de Integrações Externas</h1>
        <p className="text-sm text-slate-500">
          O CRM GLOBAL CARDS opera de forma 100% independente em banco local DBF e sincroniza com Bling,
          WhatsApp e Meta sob demanda.
        </p>
      </div>

      {/* Banner de Integração Facilitada em 1 Clique */}
      <div className="rounded-2xl bg-gradient-to-r from-[#031E44] via-[#053679] to-[#042A5F] p-6 text-white shadow-xl relative overflow-hidden border border-white/10">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-64 h-64 bg-white/5 rounded-full pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold uppercase tracking-wider border border-emerald-400/30">
              <Zap className="w-3.5 h-3.5 fill-current" /> Modo Expresso Facilitado
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Conectar e Autorizar Tudo em 1 Clique
            </h2>
            <p className="text-xs sm:text-sm text-sky-100 leading-relaxed">
              Elimine passos manuais. Clique para abrir a janela oficial de autorização do Bling com sincronização instantânea ou utilize a configuração expressa para deixar Bling, WhatsApp e Meta 100% prontos e conectados agora mesmo.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full lg:w-auto shrink-0">
            <button
              onClick={handleOpenBlingPopup}
              className="px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
              title="Abre popup oficial do Bling para login e autorização com sincronização automática"
            >
              <ExternalLink className="w-4 h-4" />
              Autorizar Bling em 1 Clique
            </button>
            <button
              disabled={expressLoading}
              onClick={handleExpressSetup}
              className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm border border-white/20 backdrop-blur-sm transition-all flex items-center justify-center gap-2"
              title="Configura e ativa Bling, WhatsApp e Meta de forma completa com parâmetros validados"
            >
              <Sparkles className={`w-4 h-4 text-amber-300 ${expressLoading ? 'animate-spin' : ''}`} />
              {expressLoading ? 'Configurando...' : 'Auto-Configurar Tudo Pronto'}
            </button>
          </div>
        </div>
      </div>

      {syncResult && (
        <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-sm text-blue-900 flex items-center justify-between">
          <span>{syncResult}</span>
          <button onClick={() => setSyncResult(null)} className="text-xs font-bold underline">
            Fechar
          </button>
        </div>
      )}

      {/* Cards de Status Atual */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {statuses.map((st) => (
          <div key={st.ID} className="satiro-card p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                {st.PROVEDOR}
              </span>
              {st.SITUACAO === 'CONECTADO' ? (
                <span className="satiro-badge bg-emerald-50 text-emerald-700">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> CONECTADO
                </span>
              ) : (
                <span className="satiro-badge bg-amber-50 text-amber-700">
                  <AlertTriangle className="w-3 h-3 mr-1" /> {st.SITUACAO}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 line-clamp-2">{st.STATUS_MSG}</p>
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
              <span>Últ. Sync: {st.ULT_SYNC || 'Nunca'}</span>
              <span>Total: {st.TOTAL_SYNC}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bling API v3 */}
        <div className="satiro-card p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-700">
                <Plug className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Bling ERP (API v3 OAuth 2.0)</h2>
                <p className="text-xs text-slate-500">
                  Sincronização de Produtos, Clientes/Contatos e Pedidos preservando campos do CRM
                </p>
              </div>
            </div>
            <button onClick={handleOpenBlingOAuth} className="satiro-btn-secondary text-xs">
              <ExternalLink className="w-3.5 h-3.5" /> Autorizar OAuth
            </button>
          </div>

          <form onSubmit={handleSaveBling} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="satiro-label">Client ID *</label>
                <input
                  required
                  value={blingForm.client_id}
                  onChange={(e) => setBlingForm({ ...blingForm, client_id: e.target.value })}
                  className="satiro-input font-mono text-xs"
                />
              </div>
              <div>
                <label className="satiro-label">Client Secret *</label>
                <div className="relative">
                  <input
                    required
                    type={showSecrets.bling_secret ? 'text' : 'password'}
                    value={blingForm.client_secret}
                    onChange={(e) => setBlingForm({ ...blingForm, client_secret: e.target.value })}
                    className="satiro-input font-mono text-xs pr-9"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('bling_secret')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
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
                <label className="satiro-label">Access Token (opcional/direto)</label>
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
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    title={showSecrets.bling_access ? 'Ocultar' : 'Visualizar'}
                  >
                    {showSecrets.bling_access ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="satiro-label">Refresh Token (opcional)</label>
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
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    title={showSecrets.bling_refresh ? 'Ocultar' : 'Visualizar'}
                  >
                    {showSecrets.bling_refresh ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <button type="submit" className="satiro-btn-primary">
                <ShieldCheck className="w-4 h-4" /> Salvar Credenciais Bling
              </button>
            </div>
          </form>

          <div className="pt-4 border-t border-slate-200 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Ações de Sincronização Manual
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                disabled={syncing}
                onClick={() => handleTriggerSync(['all'])}
                className="satiro-btn-primary text-xs justify-center"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                Sincronizar Tudo
              </button>
              <button
                disabled={syncing}
                onClick={() => handleTriggerSync(['products'])}
                className="satiro-btn-secondary text-xs justify-center"
              >
                Produtos
              </button>
              <button
                disabled={syncing}
                onClick={() => handleTriggerSync(['contacts'])}
                className="satiro-btn-secondary text-xs justify-center"
              >
                Clientes
              </button>
              <button
                disabled={syncing}
                onClick={() => handleTriggerSync(['orders'])}
                className="satiro-btn-secondary text-xs justify-center"
              >
                Pedidos
              </button>
            </div>
          </div>
        </div>

        {/* WhatsApp & Meta */}
        <div className="space-y-6">
          <div className="satiro-card p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-3">
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-700">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  WhatsApp Business Cloud API
                </h2>
                <p className="text-xs text-slate-500">
                  Envio e recebimento via Webhook `/api/whatsapp/webhook`
                </p>
              </div>
            </div>
            <form onSubmit={handleSaveWa} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="satiro-label">Phone Number ID *</label>
                  <input
                    required
                    value={waForm.phone_number_id}
                    onChange={(e) => setWaForm({ ...waForm, phone_number_id: e.target.value })}
                    className="satiro-input font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="satiro-label">Verify Token Webhook</label>
                  <div className="relative">
                    <input
                      type={showSecrets.wa_verify ? 'text' : 'password'}
                      value={waForm.verify_token}
                      onChange={(e) => setWaForm({ ...waForm, verify_token: e.target.value })}
                      className="satiro-input font-mono text-xs pr-9"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecret('wa_verify')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                      title={showSecrets.wa_verify ? 'Ocultar' : 'Visualizar'}
                    >
                      {showSecrets.wa_verify ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className="satiro-label">Permanent Access Token *</label>
                <div className="relative">
                  <input
                    required
                    type={showSecrets.wa_access ? 'text' : 'password'}
                    value={waForm.access_token}
                    onChange={(e) => setWaForm({ ...waForm, access_token: e.target.value })}
                    className="satiro-input font-mono text-xs pr-9"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('wa_access')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    title={showSecrets.wa_access ? 'Ocultar' : 'Visualizar'}
                  >
                    {showSecrets.wa_access ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div className="flex justify-end">
                <button type="submit" className="satiro-btn-primary text-xs">
                  Salvar Configuração WhatsApp
                </button>
              </div>
            </form>
          </div>

          <div className="satiro-card p-6 space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-3">
              <div className="p-2.5 rounded-lg bg-blue-50 text-blue-700">
                <Globe className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Meta Graph API Platform</h2>
                <p className="text-xs text-slate-500">
                  Credenciais de aplicativo corporativo Meta Business
                </p>
              </div>
            </div>
            <form onSubmit={handleSaveMeta} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="satiro-label">App ID *</label>
                  <input
                    required
                    value={metaForm.app_id}
                    onChange={(e) => setMetaForm({ ...metaForm, app_id: e.target.value })}
                    className="satiro-input font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="satiro-label">App Secret *</label>
                  <div className="relative">
                    <input
                      required
                      type={showSecrets.meta_secret ? 'text' : 'password'}
                      value={metaForm.app_secret}
                      onChange={(e) => setMetaForm({ ...metaForm, app_secret: e.target.value })}
                      className="satiro-input font-mono text-xs pr-9"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecret('meta_secret')}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                      title={showSecrets.meta_secret ? 'Ocultar' : 'Visualizar'}
                    >
                      {showSecrets.meta_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="satiro-label">Business ID</label>
                  <input
                    value={metaForm.business_id}
                    onChange={(e) => setMetaForm({ ...metaForm, business_id: e.target.value })}
                    className="satiro-input font-mono text-xs"
                  />
                </div>
              </div>
              <div className="flex justify-end">
                <button type="submit" className="satiro-btn-secondary text-xs">
                  Salvar Credenciais Meta
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

