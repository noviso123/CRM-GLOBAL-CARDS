import React, { useEffect, useState } from 'react';
import { Bot, Sparkles, Send, ShieldCheck, Wrench } from 'lucide-react';
import { apiRequest } from '../services/api';
import type { ClientRecord, PaginatedResponse } from '../types/crm';

interface AIChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tools?: string[];
  timestamp: string;
}

export const AIAssistantPage: React.FC = () => {
  const [clients, setClients] = useState<ClientRecord[]>([]);
  const [selectedClientId, setSelectedClientId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Olá! Sou o Copiloto Comercial do CRM GLOBAL CARDS. Tenho acesso controlado somente às ferramentas autorizadas pelo seu perfil RBAC para analisar faturamento, resumir o histórico de um cliente, sugerir follow-ups e identificar oportunidades prioritárias.',
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  useEffect(() => {
    apiRequest<PaginatedResponse<ClientRecord>>('/clients?page_size=100').then((res) =>
      setClients(res.items)
    );
  }, []);

  const sendPrompt = async (customPrompt?: string) => {
    const text = (customPrompt ?? prompt).trim();
    if (!text) return;
    setPrompt('');
    const nowStr = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { role: 'user', content: text, timestamp: nowStr }]);
    setLoading(true);
    try {
      const res = await apiRequest<{
        answer?: string;
        reply?: string;
        available_tools: string[];
      }>('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({
          prompt: text,
          client_id: selectedClientId || null,
        }),
      });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer || res.reply || '',
          tools: res.available_tools,
          timestamp: new Date().toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-blue-600" /> Inteligência Artificial Comercial
          </h1>
          <p className="text-sm text-slate-500">
            Copiloto preparado para MCP e Tool Calling com governança RBAC sem acesso direto aos
            arquivos DBF.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedClientId}
            onChange={(e) => setSelectedClientId(e.target.value)}
            className="satiro-input min-w-[240px]"
          >
            <option value="">Contexto Global do CRM</option>
            {clients.map((c) => (
              <option key={c.ID} value={c.ID}>
                Cliente: {c.NOME} ({c.CODIGO})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8 satiro-card flex flex-col h-[560px] overflow-hidden">
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/50">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${
                    m.role === 'user'
                      ? 'bg-blue-700 text-white rounded-br-none'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {m.role === 'assistant' && <Bot className="w-4 h-4 text-blue-600" />}
                    <span className="text-[11px] font-bold uppercase opacity-75">
                      {m.role === 'user' ? 'Você' : 'Global Cards AI Copilot'} • {m.timestamp}
                    </span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-xs text-slate-500 italic">
                Consultando contexto autorizado do CRM...
              </div>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendPrompt();
            }}
            className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
          >
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Pergunte sobre resumo do cliente, oportunidades prioritárias, faturamento ou sugestão de abordagem..."
              className="satiro-input flex-1"
            />
            <button type="submit" disabled={loading} className="satiro-btn-primary px-5">
              <Send className="w-4 h-4" /> Enviar
            </button>
          </form>
        </div>

        <div className="lg:col-span-4 space-y-4">
          <div className="satiro-card p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" /> Prompts Rápidos Comerciais
            </h3>
            <div className="space-y-2">
              {[
                'Gerar diagnóstico executivo de vendas, faturamento e conversão atual',
                'Resumir histórico comercial e sugerir próximo passo para o cliente selecionado',
                'Quais oportunidades abertas têm maior valor estimado para follow-up hoje?',
                'Sugerir mensagem comercial para envio de proposta e fechamento',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendPrompt(suggestion)}
                  className="w-full text-left p-2.5 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 text-xs text-slate-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>

          <div className="satiro-card p-5 space-y-2 bg-slate-900 text-slate-200">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase">
              <ShieldCheck className="w-4 h-4" /> Governança e Isolamento DBF
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              O motor de IA nunca acessa arquivos <code className="text-amber-300">.DBF</code> em
              disco. Toda consulta passa por ferramentas inspecionadas pelo módulo{' '}
              <code className="text-blue-300">CRMToolRegistry</code> respeitando as permissões do
              usuário logado.
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-[11px] text-slate-400">
              <Wrench className="w-3.5 h-3.5" /> Tools: get_dashboard_metrics, search_clients,
              search_products, list_open_opportunities
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

