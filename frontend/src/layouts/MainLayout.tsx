import React, { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  FileText,
  Filter,
  Kanban,
  LayoutDashboard,
  Link2,
  LogOut,
  MessageSquare,
  Package,
  Search,
  Settings,
  ShoppingCart,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiRequest } from '../services/api';
import { IntegrationStatusRecord, NotificationRecord } from '../types/crm';

interface NavGroup {
  title: string;
  items: Array<{
    label: string;
    path: string;
    module: string;
    icon: React.ComponentType<{ className?: string }>;
  }>;
}

const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Visão Geral',
    items: [
      { label: 'Dashboard', path: '/', module: 'DASHBOARD', icon: LayoutDashboard },
    ],
  },
  {
    title: 'Relacionamento & Catálogo',
    items: [
      { label: 'Clientes', path: '/clientes', module: 'CLIENTES', icon: Users },
      { label: 'Contatos', path: '/contatos', module: 'CONTATOS', icon: UserCheck },
      { label: 'Produtos', path: '/produtos', module: 'PRODUTOS', icon: Package },
    ],
  },
  {
    title: 'Operação Comercial',
    items: [
      { label: 'Pedidos', path: '/pedidos', module: 'PEDIDOS', icon: ShoppingCart },
      { label: 'Orçamentos', path: '/orcamentos', module: 'ORCAMENTOS', icon: FileText },
      { label: 'Oportunidades', path: '/oportunidades', module: 'OPORTUNIDADES', icon: Briefcase },
      { label: 'Funil Comercial', path: '/funil', module: 'FUNIL', icon: Kanban },
      { label: 'Atividades', path: '/atividades', module: 'ATIVIDADES', icon: Activity },
    ],
  },
  {
    title: 'Canais & Inteligência',
    items: [
      { label: 'WhatsApp', path: '/whatsapp', module: 'WHATSAPP', icon: MessageSquare },
      { label: 'Notificações', path: '/notificacoes', module: 'NOTIFICACOES', icon: Bell },
      { label: 'Integrações', path: '/integracoes', module: 'INTEGRACOES', icon: Link2 },
      { label: 'Inteligência Artificial', path: '/ia', module: 'IA', icon: Bot },
    ],
  },
  {
    title: 'Gestão & Governança',
    items: [
      { label: 'Relatórios', path: '/relatorios', module: 'RELATORIOS', icon: BarChart3 },
      { label: 'Configurações', path: '/configuracoes', module: 'CONFIGURACOES', icon: Settings },
    ],
  },
];

export const MainLayout: React.FC = () => {
  const { user, logout, hasPermission } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Record<string, any[]> | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [integrations, setIntegrations] = useState<IntegrationStatusRecord[]>([]);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTopbarStatus = async () => {
      try {
        const [notifs, intStatus] = await Promise.all([
          apiRequest<NotificationRecord[]>('/notifications?unread_only=true'),
          apiRequest<IntegrationStatusRecord[]>('/integrations/status'),
        ]);
        setUnreadCount(notifs.length);
        setIntegrations(intStatus);
      } catch {
        // silent fallback
      }
    };

    void fetchTopbarStatus();

    const handleNotificationsUpdated = () => {
      void fetchTopbarStatus();
    };

    window.addEventListener('crm-notifications-updated', handleNotificationsUpdated);
    window.addEventListener('storage', handleNotificationsUpdated);
    const interval = setInterval(fetchTopbarStatus, 20000);

    return () => {
      window.removeEventListener('crm-notifications-updated', handleNotificationsUpdated);
      window.removeEventListener('storage', handleNotificationsUpdated);
      clearInterval(interval);
    };
  }, [location.pathname]);

  useEffect(() => {
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSearchResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await apiRequest<Record<string, any[]>>(
          `/search?q=${encodeURIComponent(q)}`
        );
        setSearchResults(res);
        setSearchOpen(true);
      } catch {
        setSearchResults(null);
      }
    }, 220);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const blingStatus = integrations.find((i) => i.PROVEDOR === 'BLING')?.SITUACAO || 'DESCONECTADO';
  const waStatus = integrations.find((i) => i.PROVEDOR === 'WHATSAPP')?.SITUACAO || 'DESCONECTADO';

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900">
      {/* Sidebar Lateral */}
      <aside
        className={`${
          collapsed ? 'w-20' : 'w-64'
        } bg-[#053679] text-white flex flex-col transition-all duration-200 shrink-0 shadow-xl z-20`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/10 bg-[#03224C]">
          {!collapsed && (
            <Link to="/" className="flex items-center gap-2.5 overflow-hidden">
              <div className="bg-white rounded-lg p-1 shrink-0 shadow-sm flex items-center justify-center">
                <img
                  src="/logo-globalcards.jpg"
                  alt="Global Cards"
                  className="h-7 w-auto object-contain"
                />
              </div>
              <div className="truncate">
                <span className="font-extrabold tracking-tight text-xs block leading-tight text-white">
                  CRM GLOBAL CARDS
                </span>
                <span className="text-[10px] text-blue-200 block truncate">
                  Gestão Comercial + Bling
                </span>
              </div>
            </Link>
          )}
          {collapsed && (
            <Link
              to="/"
              className="bg-white p-1 mx-auto rounded-lg shadow-sm flex items-center justify-center"
              title="CRM GLOBAL CARDS"
            >
              <img
                src="/logo-globalcards.jpg"
                alt="GC"
                className="h-6 w-6 object-contain"
              />
            </Link>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? 'Expandir menu' : 'Recolher menu'}
            className="p-1.5 rounded-md hover:bg-white/10 text-blue-100"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2.5 space-y-4">
          {NAV_GROUPS.map((group) => {
            const visibleItems = group.items.filter((it) => hasPermission(it.module, 'view'));
            if (visibleItems.length === 0) return null;
            return (
              <div key={group.title}>
                {!collapsed && (
                  <div className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-blue-200/70">
                    {group.title}
                  </div>
                )}
                <div className="space-y-0.5">
                  {visibleItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                            isActive
                              ? 'bg-[#ED6706] text-white font-bold shadow-sm'
                              : 'text-blue-100/90 hover:bg-white/10 hover:text-white'
                          }`
                        }
                        title={collapsed ? item.label : undefined}
                      >
                        <Icon className="w-4 h-4 shrink-0" />
                        {!collapsed && <span className="truncate">{item.label}</span>}
                        {!collapsed && item.path === '/notificacoes' && unreadCount > 0 && (
                          <span className="ml-auto bg-[#ED6706] text-white text-[11px] font-bold px-1.5 py-0.5 rounded-full shadow-2xs">
                            {unreadCount}
                          </span>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        <div className="p-3 border-t border-white/10 bg-[#03224C]">
          {!collapsed ? (
            <div className="flex items-center justify-between">
              <div className="truncate">
                <p className="text-xs font-semibold text-white truncate">{user?.NOME}</p>
                <p className="text-[11px] text-sky-200 truncate">
                  {user?.PERFIL} • Alçada {user?.DESC_MAX}%
                </p>
              </div>
              <button
                type="button"
                onClick={logout}
                title="Sair do sistema"
                className="p-2 rounded-lg hover:bg-white/10 text-sky-200 hover:text-white"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={logout}
              title="Sair do sistema"
              className="w-full flex justify-center p-2 rounded-lg hover:bg-white/10 text-sky-200"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Área Principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Cabeçalho Superior */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between gap-4 sticky top-0 z-10 shadow-sm">
          {/* Pesquisa Global */}
          <div className="relative flex-1 max-w-xl">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => searchResults && setSearchOpen(true)}
              placeholder="Pesquisa global (Clientes, CPF/CNPJ, Produtos, Pedidos, Oportunidades)..."
              className="w-full pl-10 pr-9 py-2 text-sm bg-slate-100 hover:bg-slate-100/80 focus:bg-white rounded-lg border border-transparent focus:border-sky-500 focus:outline-none transition"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults(null);
                  setSearchOpen(false);
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Dropdown de Resultados da Pesquisa Global */}
            {searchOpen && searchResults && (
              <div className="absolute left-0 right-0 top-12 bg-white rounded-xl shadow-2xl border border-slate-200 max-h-[70vh] overflow-y-auto p-4 z-50 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-semibold uppercase text-slate-500">
                    Resultados Indexados (.IDX)
                  </span>
                  <button
                    type="button"
                    onClick={() => setSearchOpen(false)}
                    className="text-xs text-slate-400 hover:text-slate-700"
                  >
                    Fechar
                  </button>
                </div>

                {(
                  [
                    ['clients', 'Clientes', '/clientes'],
                    ['products', 'Produtos', '/produtos'],
                    ['orders', 'Pedidos', '/pedidos'],
                    ['quotations', 'Orçamentos', '/orcamentos'],
                    ['opportunities', 'Oportunidades', '/funil'],
                    ['contacts', 'Contatos', '/contatos'],
                    ['activities', 'Atividades', '/atividades'],
                    ['conversations', 'Conversas WhatsApp', '/whatsapp'],
                  ] as const
                ).map(([key, label, targetRoute]) => {
                  const list = searchResults[key] || [];
                  if (list.length === 0) return null;
                  return (
                    <div key={key}>
                      <p className="text-[11px] font-bold uppercase text-sky-700 mb-1">{label}</p>
                      <div className="space-y-1">
                        {list.map((item: any) => (
                          <button
                            key={item.ID}
                            type="button"
                            onClick={() => {
                              setSearchOpen(false);
                              navigate(targetRoute);
                            }}
                            className="w-full text-left px-3 py-1.5 rounded-lg hover:bg-slate-100 text-xs flex items-center justify-between"
                          >
                            <span className="font-medium text-slate-800">
                              {item.NOME || item.TITULO || item.NUMERO || item.NOME_CONT}
                            </span>
                            <span className="font-mono text-[11px] text-slate-500">
                              {item.CODIGO || item.CPF_CNPJ || item.TELEFONE || item.SITUACAO}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Indicadores de Integração, Notificações e Perfil */}
          <div className="flex items-center gap-3">
            <Link
              to="/integracoes"
              className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-200 bg-slate-50 hover:bg-slate-100"
              title="Status da integração Bling API v3"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  blingStatus === 'CONECTADO' ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
              <span>Bling: {blingStatus}</span>
            </Link>

            <Link
              to="/whatsapp"
              className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-200 bg-slate-50 hover:bg-slate-100"
              title="Status da integração WhatsApp Cloud API"
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  waStatus === 'CONECTADO' ? 'bg-emerald-500' : 'bg-slate-400'
                }`}
              />
              <span>WhatsApp: {waStatus}</span>
            </Link>

            <Link
              to="/notificacoes"
              className="relative p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              title="Centro de Notificações"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-orange-600 text-white text-[10px] font-bold flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Link>

            <Link
              to="/configuracoes"
              className="flex items-center gap-2 pl-3 border-l border-slate-200 text-xs font-medium text-slate-700 hover:text-sky-700"
            >
              <div className="w-8 h-8 rounded-full bg-[#053679] text-white ring-2 ring-[#ED6706]/40 flex items-center justify-center font-bold">
                {user?.NOME?.charAt(0) || 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <span className="block font-semibold text-slate-800 leading-tight">
                  {user?.NOME}
                </span>
                <span className="block text-[11px] text-slate-500">{user?.EMAIL}</span>
              </div>
            </Link>
          </div>
        </header>

        {/* Conteúdo das Páginas */}
        <main className="flex-1 p-6 overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

