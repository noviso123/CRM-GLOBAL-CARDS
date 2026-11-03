import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiRequest, getStoredToken, setStoredToken } from '../services/api';
import { ModulePermission, UserRecord } from '../types/crm';

interface AuthContextValue {
  user: UserRecord | null;
  permissions: Record<string, ModulePermission>;
  loading: boolean;
  login: (loginOrEmail: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (moduleName: string, action?: keyof ModulePermission) => boolean;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserRecord | null>(null);
  const [permissions, setPermissions] = useState<Record<string, ModulePermission>>({});
  const [loading, setLoading] = useState<boolean>(true);

  const refreshMe = async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setPermissions({});
      setLoading(false);
      return;
    }
    try {
      const data = await apiRequest<{
        user: UserRecord;
        permissions: Record<string, ModulePermission>;
      }>('/auth/me');
      setUser(data.user);
      setPermissions(data.permissions || {});
    } catch {
      setStoredToken(null);
      setUser(null);
      setPermissions({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshMe();
  }, []);

  const login = async (loginOrEmail: string, password: string) => {
    const data = await apiRequest<{
      access_token: string;
      user: UserRecord;
      permissions: Record<string, ModulePermission>;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ login: loginOrEmail, password }),
    });
    setStoredToken(data.access_token);
    setUser(data.user);
    setPermissions(data.permissions || {});
  };

  const logout = () => {
    void apiRequest('/auth/logout', { method: 'POST' }).catch(() => {});
    setStoredToken(null);
    setUser(null);
    setPermissions({});
  };

  const hasPermission = (
    moduleName: string,
    action: keyof ModulePermission = 'view'
  ): boolean => {
    if (!user) return false;
    if (user.PERFIL === 'ADMIN') return true;
    const mod = permissions[moduleName.toUpperCase()];
    return mod ? Boolean(mod[action]) : true;
  };

  return (
    <AuthContext.Provider
      value={{ user, permissions, loading, login, logout, hasPermission, refreshMe }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth deve ser utilizado dentro de AuthProvider');
  }
  return ctx;
}

