import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, ShieldCheck, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiRequest } from '../services/api';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState('admin');
  const [password, setPassword] = useState('GlobalCards@2026');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [recoverMode, setRecoverMode] = useState(false);
  const [recoverEmail, setRecoverEmail] = useState('');
  const [recoverMessage, setRecoverMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(identifier, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Falha na autenticação.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRecover = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await apiRequest<{ message: string }>('/auth/recover-password', {
        method: 'POST',
        body: JSON.stringify({ email: recoverEmail }),
      });
      setRecoverMessage(res.message);
    } catch (err: any) {
      setError(err.message || 'Erro ao solicitar recuperação.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#071E38] via-[#0F3D6E] to-[#0284C7] p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
        <div className="bg-[#0F3D6E] px-8 py-7 text-white">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-sky-500 flex items-center justify-center font-extrabold text-base shadow">
              GC
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">CRM GLOBAL CARDS</h1>
              <p className="text-xs text-sky-200">
                Plataforma Comercial Independente + Integração Bling
              </p>
            </div>
          </div>
        </div>

        <div className="p-8">
          {!recoverMode ? (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Acesso ao Sistema</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Execução 100% local com armazenamento seguro em DBF.
                </p>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 font-medium">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Usuário ou E-mail
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600"
                    placeholder="admin ou admin@globalcards.com.br"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Senha
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-sky-600 transition"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                    title={showPassword ? 'Ocultar senha' : 'Ver senha'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 px-4 rounded-lg bg-[#0F3D6E] hover:bg-[#0B2D52] text-white font-semibold text-sm transition shadow-md disabled:opacity-50"
              >
                {submitting ? 'Autenticando...' : 'Entrar no CRM GLOBAL CARDS'}
              </button>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                <button
                  type="button"
                  onClick={() => setRecoverMode(true)}
                  className="text-sky-700 hover:underline font-medium"
                >
                  Recuperar senha
                </button>
                <span className="inline-flex items-center gap-1 text-slate-400">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> 127.0.0.1 Local
                </span>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRecover} className="space-y-4">
              <h2 className="text-lg font-bold text-slate-900">Recuperação de Senha</h2>
              <p className="text-xs text-slate-600">
                Informe seu e-mail cadastrado para registrar a solicitação local de redefinição.
              </p>
              {recoverMessage && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800">
                  {recoverMessage}
                </div>
              )}
              <input
                type="email"
                required
                value={recoverEmail}
                onChange={(e) => setRecoverEmail(e.target.value)}
                placeholder="seu.email@empresa.com.br"
                className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setRecoverMode(false);
                    setRecoverMessage(null);
                  }}
                  className="flex-1 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700"
                >
                  Voltar ao login
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-lg bg-sky-600 text-white text-xs font-semibold"
                >
                  Solicitar
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

