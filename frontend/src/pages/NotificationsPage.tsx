import React, { useEffect, useState } from 'react';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { apiRequest } from '../services/api';
import type { NotificationRecord } from '../types/crm';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<NotificationRecord[]>(
        `/notifications?unread_only=${unreadOnly}`
      );
      setNotifications(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [unreadOnly]);

  const markRead = async (id: string) => {
    await apiRequest(`/notifications/${id}/read`, { method: 'PATCH' });
    await loadNotifications();
  };

  const markAllRead = async () => {
    await apiRequest('/notifications/read-all', { method: 'POST' });
    await loadNotifications();
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Central de Notificações</h1>
          <p className="text-sm text-slate-500">
            Alertas de novos pedidos, orçamentos vencendo, mensagens e sincronizações Bling.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={unreadOnly ? 'satiro-btn-primary' : 'satiro-btn-secondary'}
          >
            {unreadOnly ? 'Exibindo Não Lidas' : 'Filtrar Não Lidas'}
          </button>
          <button onClick={markAllRead} className="satiro-btn-secondary">
            <CheckCheck className="w-4 h-4" /> Marcar Todas como Lidas
          </button>
        </div>
      </div>

      <div className="satiro-card divide-y divide-slate-200">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Carregando notificações...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Bell className="w-10 h-10 mx-auto mb-2 stroke-1" />
            <p className="text-sm">Nenhuma notificação para exibir.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.ID}
              className={`p-4 flex items-start justify-between gap-4 ${
                !n.LIDA ? 'bg-blue-50/40' : 'bg-white'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  {!n.LIDA && <span className="w-2 h-2 rounded-full bg-blue-600" />}
                  <span className="satiro-badge bg-slate-100 text-slate-700">{n.TIPO}</span>
                  <h3 className="text-sm font-bold text-slate-900">{n.TITULO}</h3>
                </div>
                <p className="text-sm text-slate-600">{n.MENSAGEM}</p>
                <p className="text-xs text-slate-400">
                  Data: {n.DT_CRIA} {n.DT_LEITURA ? `• Lida em ${n.DT_LEITURA}` : ''}
                </p>
              </div>
              {!n.LIDA && (
                <button
                  onClick={() => markRead(n.ID)}
                  className="satiro-btn-secondary py-1 px-2.5 text-xs shrink-0"
                >
                  <Check className="w-3.5 h-3.5" /> Marcar lida
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

