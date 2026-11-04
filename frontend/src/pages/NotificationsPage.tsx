import React, { useEffect, useState } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Filter,
  Inbox,
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type { NotificationRecord } from '../types/crm';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const notifyBadgeUpdate = () => {
    window.dispatchEvent(new CustomEvent('crm-notifications-updated'));
  };

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<NotificationRecord[]>(
        `/notifications?unread_only=${unreadOnly}`
      );
      setNotifications(data || []);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadNotifications();
  }, [unreadOnly]);

  const markRead = async (id: string) => {
    // Atualização otimista imediata
    setNotifications((prev) =>
      prev.map((n) => (n.ID === id ? { ...n, LIDA: true, DT_LEITURA: 'Agora' } : n))
    );
    notifyBadgeUpdate();

    try {
      await apiRequest(`/notifications/${id}/read`, { method: 'PATCH' });
    } catch {
      // rollback se necessário
    } finally {
      notifyBadgeUpdate();
      await loadNotifications();
    }
  };

  const markAllRead = async () => {
    setActionLoading(true);
    // Atualização otimista imediata
    setNotifications((prev) => prev.map((n) => ({ ...n, LIDA: true, DT_LEITURA: 'Agora' })));
    notifyBadgeUpdate();

    try {
      await apiRequest('/notifications/read-all', { method: 'POST' });
    } catch {
      // fallback
    } finally {
      setActionLoading(false);
      notifyBadgeUpdate();
      await loadNotifications();
    }
  };

  const deleteNotification = async (id: string) => {
    // Atualização otimista imediata
    setNotifications((prev) => prev.filter((n) => n.ID !== id));
    notifyBadgeUpdate();

    try {
      await apiRequest(`/notifications/${id}`, { method: 'DELETE' });
    } catch {
      // fallback
    } finally {
      notifyBadgeUpdate();
      await loadNotifications();
    }
  };

  const clearAllNotifications = async () => {
    if (notifications.length === 0) return;
    const confirmClear = window.confirm(
      'Tem certeza que deseja excluir e limpar todas as notificações definitivamente?'
    );
    if (!confirmClear) return;

    setActionLoading(true);
    // Limpeza otimista imediata
    setNotifications([]);
    notifyBadgeUpdate();

    try {
      await apiRequest('/notifications/clear-all', { method: 'POST' });
    } catch {
      // fallback
    } finally {
      setActionLoading(false);
      notifyBadgeUpdate();
      await loadNotifications();
    }
  };

  const unreadTotal = notifications.filter((n) => !n.LIDA).length;

  const getBadgeStyle = (tipo: string) => {
    const t = (tipo || '').toUpperCase();
    if (t.includes('PEDIDO') || t.includes('VENDA')) {
      return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    }
    if (t.includes('BLING') || t.includes('SYNC')) {
      return 'bg-blue-100 text-blue-800 border-blue-200';
    }
    if (t.includes('WHATSAPP') || t.includes('CHAT')) {
      return 'bg-teal-100 text-teal-800 border-teal-200';
    }
    if (t.includes('ERRO') || t.includes('ALERTA')) {
      return 'bg-rose-100 text-rose-800 border-rose-200';
    }
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Central de Notificações</h1>
            {unreadTotal > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-[#ED6706] text-white animate-pulse">
                {unreadTotal} não lida{unreadTotal > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500">
            Acompanhe em tempo real alertas de vendas, sincronizações do Bling, mensagens e tarefas.
          </p>
        </div>

        {/* Botões de Ação Global */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-1.5 transition-all shadow-2xs ${
              unreadOnly
                ? 'bg-[#053679] text-white shadow-md'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            {unreadOnly ? 'Exibindo Somente Não Lidas' : 'Filtrar Não Lidas'}
          </button>

          <button
            type="button"
            disabled={actionLoading || unreadTotal === 0}
            onClick={markAllRead}
            className="px-3.5 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-emerald-700 transition-all shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed"
            title="Marcar todas as notificações como lidas"
          >
            <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
            Marcar Todas como Lidas
          </button>

          <button
            type="button"
            disabled={actionLoading || notifications.length === 0}
            onClick={clearAllNotifications}
            className="px-3.5 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-1.5 bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 hover:border-rose-300 transition-all shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed"
            title="Excluir e limpar todas as notificações"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-600" />
            Limpar Todas
          </button>
        </div>
      </div>

      {/* Lista de Notificações */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
            <div className="w-6 h-6 border-2 border-[#053679] border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-medium">Carregando notificações indexadas...</span>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-16 text-center text-slate-400 flex flex-col items-center justify-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center mb-3 text-slate-400">
              <Inbox className="w-7 h-7 stroke-1" />
            </div>
            <h3 className="text-base font-bold text-slate-700">Tudo limpo por aqui!</h3>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              {unreadOnly
                ? 'Nenhuma notificação não lida no momento.'
                : 'Você não possui notificações pendentes ou alertas ativos.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((n) => {
              const isUnread = !n.LIDA;
              return (
                <div
                  key={n.ID}
                  className={`p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors ${
                    isUnread
                      ? 'bg-blue-50/40 hover:bg-blue-50/70 border-l-4 border-l-[#ED6706]'
                      : 'bg-white hover:bg-slate-50/80 border-l-4 border-l-transparent'
                  }`}
                >
                  <div className="flex items-start gap-3.5 min-w-0 flex-1">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                        isUnread
                          ? 'bg-[#053679] text-white shadow-sm'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      <Bell className="w-4 h-4" />
                    </div>

                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider border ${getBadgeStyle(
                            n.TIPO
                          )}`}
                        >
                          {n.TIPO || 'NOTIFICAÇÃO'}
                        </span>
                        <h3
                          className={`text-sm tracking-tight truncate ${
                            isUnread ? 'font-black text-slate-900' : 'font-semibold text-slate-700'
                          }`}
                        >
                          {n.TITULO}
                        </h3>
                        {isUnread && (
                          <span className="w-2 h-2 rounded-full bg-[#ED6706] shrink-0" title="Não lida" />
                        )}
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed break-words">
                        {n.MENSAGEM}
                      </p>

                      <div className="flex items-center gap-3 text-[11px] text-slate-400 pt-0.5">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {n.DT_CRIA || 'Data recente'}
                        </span>
                        {n.LIDA && n.DT_LEITURA && (
                          <span className="text-slate-400">
                            • Visualizada {n.DT_LEITURA}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Ações por Item */}
                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    {isUnread && (
                      <button
                        type="button"
                        onClick={() => markRead(n.ID)}
                        className="px-3 py-1.5 rounded-lg text-xs font-bold inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-all active:scale-95"
                        title="Marcar como vista/lida"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Marcar vista</span>
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => deleteNotification(n.ID)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-all"
                      title="Excluir esta notificação"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
