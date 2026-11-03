import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ClientsPage } from './pages/ClientsPage';
import { ContactsPage } from './pages/ContactsPage';
import { ProductsCatalogPage } from './pages/ProductsCatalogPage';
import { OrdersPage } from './pages/OrdersPage';
import { QuotationsPage } from './pages/QuotationsPage';
import { OpportunitiesFunnelPage } from './pages/OpportunitiesFunnelPage';
import { WhatsAppPage } from './pages/WhatsAppPage';
import { ActivitiesPage } from './pages/ActivitiesPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const ProtectedRoutes: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white text-sm">
        Inicializando CRM GLOBAL CARDS + Bling...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/clientes" element={<ClientsPage />} />
        <Route path="/contatos" element={<ContactsPage />} />
        <Route path="/produtos" element={<ProductsCatalogPage />} />
        <Route path="/pedidos" element={<OrdersPage />} />
        <Route path="/orcamentos" element={<QuotationsPage />} />
        <Route path="/oportunidades" element={<OpportunitiesFunnelPage />} />
        <Route path="/funil" element={<OpportunitiesFunnelPage />} />
        <Route path="/whatsapp" element={<WhatsAppPage />} />
        <Route path="/atividades" element={<ActivitiesPage />} />
        <Route path="/notificacoes" element={<NotificationsPage />} />
        <Route path="/integracoes" element={<IntegrationsPage />} />
        <Route path="/ia" element={<AIAssistantPage />} />
        <Route path="/relatorios" element={<ReportsPage />} />
        <Route path="/configuracoes" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;

