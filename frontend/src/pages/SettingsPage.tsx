import React, { useEffect, useState } from 'react';
import {
  Users,
  Shield,
  Database,
  HardDriveDownload,
  RefreshCw,
  CheckCircle2,
  KeyRound,
  Plus,
  FileSpreadsheet,
  Eye,
  EyeOff,
} from 'lucide-react';
import { apiRequest } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import type { UserRecord, HistoryRecord } from '../types/crm';

interface PermissionRow {
  ID: string;
  PERFIL: string;
  MODULO: string;
  P_VER: boolean;
  P_CRIAR: boolean;
  P_EDITAR: boolean;
  P_EXCLUIR: boolean;
  P_EXPORT: boolean;
}

interface BackupItem {
  backup_id: string;
  created_at: string;
  description: string;
  tables_count: number;
  zip_filename: string;
}

interface DBFTableDiag {
  exists: boolean;
  valid_signature: boolean;
  header_records: number;
  active_records: number;
  deleted_records: number;
  incomplete_transaction_flag: boolean;
  corrupted: boolean;
}

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    'users' | 'permissions' | 'backups' | 'dbf_diag' | 'audit' | 'password'
  >('dbf_diag');
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [permissions, setPermissions] = useState<PermissionRow[]>([]);
  const [backups, setBackups] = useState<BackupItem[]>([]);
  const [dbfDiag, setDbfDiag] = useState<Record<string, DBFTableDiag>>({});
  const [auditLogs, setAuditLogs] = useState<{
    audit_entries: Array<Record<string, unknown>>;
    commercial_history: HistoryRecord[];
  }>({ audit_entries: [], commercial_history: [] });
  const [feedback, setFeedback] = useState<string | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const toggleSecret = (field: string) => {
    setShowSecrets((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const [newUser, setNewUser] = useState({
    NOME: '',
    LOGIN: '',
    EMAIL: '',
    PASSWORD: '',
    PERFIL: 'VENDEDOR',
    CARGO: 'Consultor Comercial',
    DESC_MAX: 10,
  });

  const [pwdForm, setPwdForm] = useState({
    current_password: '',
    new_password: '',
  });

  const loadData = async () => {
    const [uList, pList, bList, diagRes, logsRes] = await Promise.all([
      apiRequest<UserRecord[]>('/settings/users'),
      apiRequest<PermissionRow[]>('/settings/permissions'),
      apiRequest<BackupItem[]>('/settings/backup/list'),
      apiRequest<{ tables: Record<string, DBFTableDiag> }>('/settings/diagnostics/verify-dbf'),
      apiRequest<{
        audit_entries: Array<Record<string, unknown>>;
        commercial_history: HistoryRecord[];
      }>('/settings/audit-logs'),
    ]);
    setUsers(uList);
    setPermissions(pList);
    setBackups(bList);
    setDbfDiag(diagRes.tables);
    setAuditLogs(logsRes);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiRequest('/settings/users', {
      method: 'POST',
      body: JSON.stringify(newUser),
    });
    setNewUser({
      NOME: '',
      LOGIN: '',
      EMAIL: '',
      PASSWORD: '',
      PERFIL: 'VENDEDOR',
      CARGO: 'Consultor Comercial',
      DESC_MAX: 10,
    });
    setFeedback('Novo usuário criado com sucesso na tabela USUARIOS.DBF.');
    await loadData();
  };

  const handleTogglePerm = async (
    row: PermissionRow,
    field: 'P_VER' | 'P_CRIAR' | 'P_EDITAR' | 'P_EXCLUIR' | 'P_EXPORT'
  ) => {
    const updated = { ...row, [field]: !row[field] };
    await apiRequest('/settings/permissions', {
      method: 'PUT',
      body: JSON.stringify(updated),
    });
    setPermissions((prev) => prev.map((r) => (r.ID === row.ID ? updated : r)));
  };

  const handleCreateBackup = async () => {
    const res = await apiRequest<BackupItem>('/settings/backup/create', {
      method: 'POST',
      body: JSON.stringify({ description: 'Backup manual completo (.DBF + manifesto SHA-256)' }),
    });
    setFeedback(`Backup ${res.backup_id} gerado com sucesso (${res.tables_count} tabelas DBF).`);
    await loadData();
  };

  const handleRestoreBackup = async (backupId: string) => {
    if (!window.confirm(`Restaurar o backup ${backupId}? Um ponto de segurança prévio será criado.`))
      return;
    await apiRequest('/settings/backup/restore', {
      method: 'POST',
      body: JSON.stringify({ backup_id: backupId }),
    });
    setFeedback(`Backup ${backupId} restaurado e índices .IDX reconstruídos com sucesso.`);
    await loadData();
  };

  const handleRebuildIndexes = async () => {
    await apiRequest('/settings/diagnostics/rebuild-indexes', { method: 'POST' });
    setFeedback('Todos os 21 arquivos de índice secundário (.IDX) foram reconstruídos com CRC32.');
    await loadData();
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify(pwdForm),
      });
      setPwdForm({ current_password: '', new_password: '' });
      setFeedback('Senha alterada com sucesso.');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao alterar senha');
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Configurações, Segurança e Motor DBF
        </h1>
        <p className="text-sm text-slate-500">
          Administração de usuários, matriz RBAC, backups consistentes e diagnóstico das 21 tabelas
          dBase III+.
        </p>
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-medium text-emerald-900 flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="underline font-bold">
            OK
          </button>
        </div>
      )}

      <div className="bg-slate-100/80 p-1.5 rounded-xl border border-slate-200/80 flex flex-wrap gap-1.5 shadow-sm">
        {[
          { id: 'dbf_diag', label: 'Diagnóstico Motor DBF (21 Tabelas)', icon: Database },
          { id: 'backups', label: 'Backups & Restauração ZIP', icon: HardDriveDownload },
          { id: 'users', label: 'Usuários e Alçadas', icon: Users },
          { id: 'permissions', label: 'Matriz de Permissões (RBAC)', icon: Shield },
          { id: 'audit', label: 'Logs de Auditoria', icon: FileSpreadsheet },
          { id: 'password', label: 'Minha Conta & Senha', icon: KeyRound },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as typeof activeTab)}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold inline-flex items-center gap-2 transition-all ${
                activeTab === t.id
                  ? 'bg-blue-700 text-white shadow-sm'
                  : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-white/80 border border-slate-200/60'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'dbf_diag' && (
        <div className="space-y-4">
          <div className="satiro-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 text-white">
            <div>
              <h2 className="text-sm font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Motor Nativo GlobalCardsDBFEngine — dBase III+ (Assinatura 0x03 / CP1252)
              </h2>
              <p className="text-xs text-slate-300 mt-0.5">
                Zero SQL (Sem SQLite/PostgreSQL/MySQL). Armazenamento 100% local em{' '}
                <code>data/dbf/*.DBF</code> com índices <code>.IDX</code>.
              </p>
            </div>
            <button onClick={handleRebuildIndexes} className="satiro-btn-primary shrink-0 text-xs">
              <RefreshCw className="w-3.5 h-3.5" /> Reindexar Todas as 21 Tabelas (.IDX)
            </button>
          </div>

          <div className="satiro-card overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase">
                  <th className="py-3 px-4">Arquivo .DBF</th>
                  <th className="py-3 px-4">Assinatura 0x03</th>
                  <th className="py-3 px-4">Registros Ativos</th>
                  <th className="py-3 px-4">Deletados Lógicos (0x2A)</th>
                  <th className="py-3 px-4">Flag Transação (Byte 14)</th>
                  <th className="py-3 px-4">Saúde Física</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs">
                {Object.entries(dbfDiag).map(([tableName, info]) => (
                  <tr key={tableName} className="hover:bg-slate-50">
                    <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                      {tableName}.DBF
                    </td>
                    <td className="py-2.5 px-4">
                      {info.valid_signature ? (
                        <span className="text-emerald-700 font-semibold">Válida (0x03)</span>
                      ) : (
                        <span className="text-red-600 font-semibold">Inválida</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-bold text-blue-700">{info.active_records}</td>
                    <td className="py-2.5 px-4 text-slate-500">{info.deleted_records}</td>
                    <td className="py-2.5 px-4">
                      {info.incomplete_transaction_flag ? 'Pendente (0x01)' : 'Limpa (0x00)'}
                    </td>
                    <td className="py-2.5 px-4">
                      {!info.corrupted ? (
                        <span className="satiro-badge bg-emerald-50 text-emerald-700">
                          ÍNTEGRO
                        </span>
                      ) : (
                        <span className="satiro-badge bg-red-50 text-red-700">CORROMPIDO</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'backups' && (
        <div className="space-y-4">
          <div className="satiro-card p-5 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Cópias de Segurança Consistentes (.ZIP + Manifesto SHA-256)
              </h3>
              <p className="text-xs text-slate-500">
                Inclui todos os 21 arquivos .DBF, índices .IDX e documentos JSON com bloqueio
                coordenado de escrita.
              </p>
            </div>
            <button onClick={handleCreateBackup} className="satiro-btn-primary">
              <HardDriveDownload className="w-4 h-4" /> Criar Backup Agora
            </button>
          </div>

          <div className="satiro-card divide-y divide-slate-200">
            {backups.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                Nenhum backup criado até o momento.
              </div>
            ) : (
              backups.map((b) => (
                <div key={b.backup_id} className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold text-slate-900 font-mono">{b.backup_id}</p>
                    <p className="text-xs text-slate-600">{b.description}</p>
                    <p className="text-[11px] text-slate-400">
                      Criado em: {b.created_at} • {b.tables_count} tabelas verificadas
                    </p>
                  </div>
                  <button
                    onClick={() => handleRestoreBackup(b.backup_id)}
                    className="satiro-btn-secondary text-xs"
                  >
                    Restaurar Backup
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-8 satiro-card overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase">
                  <th className="py-3 px-4">Nome</th>
                  <th className="py-3 px-4">Login / E-mail</th>
                  <th className="py-3 px-4">Perfil</th>
                  <th className="py-3 px-4">Desc. Máx (%)</th>
                  <th className="py-3 px-4">Situação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs">
                {users.map((u) => (
                  <tr key={u.ID}>
                    <td className="py-3 px-4 font-bold text-slate-900">{u.NOME}</td>
                    <td className="py-3 px-4 text-slate-600">
                      {u.LOGIN} • {u.EMAIL}
                    </td>
                    <td className="py-3 px-4">
                      <span className="satiro-badge bg-blue-50 text-blue-700">{u.PERFIL}</span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold">{u.DESC_MAX}%</td>
                    <td className="py-3 px-4">
                      <span className="satiro-badge bg-emerald-50 text-emerald-700">
                        {u.SITUACAO}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="lg:col-span-4 satiro-card p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Plus className="w-4 h-4 text-blue-600" /> Cadastrar Novo Usuário
            </h3>
            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="satiro-label">Nome Completo *</label>
                <input
                  required
                  value={newUser.NOME}
                  onChange={(e) => setNewUser({ ...newUser, NOME: e.target.value })}
                  className="satiro-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="satiro-label">Login *</label>
                  <input
                    required
                    value={newUser.LOGIN}
                    onChange={(e) => setNewUser({ ...newUser, LOGIN: e.target.value })}
                    className="satiro-input"
                  />
                </div>
                <div>
                  <label className="satiro-label">Senha Inicial *</label>
                  <div className="relative">
                    <input
                      required
                      type={showSecrets['newUserPassword'] ? 'text' : 'password'}
                      value={newUser.PASSWORD}
                      onChange={(e) => setNewUser({ ...newUser, PASSWORD: e.target.value })}
                      className="satiro-input pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => toggleSecret('newUserPassword')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                      title={showSecrets['newUserPassword'] ? 'Ocultar senha' : 'Exibir senha'}
                    >
                      {showSecrets['newUserPassword'] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <label className="satiro-label">E-mail *</label>
                <input
                  required
                  type="email"
                  value={newUser.EMAIL}
                  onChange={(e) => setNewUser({ ...newUser, EMAIL: e.target.value })}
                  className="satiro-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="satiro-label">Perfil RBAC</label>
                  <select
                    value={newUser.PERFIL}
                    onChange={(e) => setNewUser({ ...newUser, PERFIL: e.target.value })}
                    className="satiro-input"
                  >
                    <option value="ADMIN">ADMIN</option>
                    <option value="GERENTE">GERENTE</option>
                    <option value="VENDEDOR">VENDEDOR</option>
                    <option value="ATENDIMENTO">ATENDIMENTO</option>
                    <option value="FINANCEIRO">FINANCEIRO</option>
                  </select>
                </div>
                <div>
                  <label className="satiro-label">Desconto Máx (%)</label>
                  <input
                    type="number"
                    value={newUser.DESC_MAX}
                    onChange={(e) => setNewUser({ ...newUser, DESC_MAX: Number(e.target.value) })}
                    className="satiro-input"
                  />
                </div>
              </div>
              <button type="submit" className="satiro-btn-primary w-full justify-center">
                Criar Usuário
              </button>
            </form>
          </div>
        </div>
      )}

      {activeTab === 'permissions' && (
        <div className="satiro-card overflow-hidden">
          <div className="max-h-[540px] overflow-y-auto">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase">
                <tr>
                  <th className="py-3 px-4">Perfil</th>
                  <th className="py-3 px-4">Módulo</th>
                  <th className="py-3 px-4 text-center">Visualizar</th>
                  <th className="py-3 px-4 text-center">Criar</th>
                  <th className="py-3 px-4 text-center">Editar</th>
                  <th className="py-3 px-4 text-center">Excluir</th>
                  <th className="py-3 px-4 text-center">Exportar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs">
                {permissions.map((p) => (
                  <tr key={p.ID} className="hover:bg-slate-50">
                    <td className="py-2 px-4 font-bold text-slate-800">{p.PERFIL}</td>
                    <td className="py-2 px-4 font-mono text-slate-600">{p.MODULO}</td>
                    {(['P_VER', 'P_CRIAR', 'P_EDITAR', 'P_EXCLUIR', 'P_EXPORT'] as const).map(
                      (field) => (
                        <td key={field} className="py-2 px-4 text-center">
                          <input
                            type="checkbox"
                            checked={p[field]}
                            onChange={() => handleTogglePerm(p, field)}
                            className="w-4 h-4 accent-blue-700 rounded cursor-pointer"
                          />
                        </td>
                      )
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="satiro-card p-5 space-y-3">
          <h3 className="text-sm font-bold text-slate-900">
            Histórico Comercial e Auditoria (HISTORIC.DBF & audit.jsonl)
          </h3>
          <div className="divide-y divide-slate-200 max-h-[480px] overflow-y-auto">
            {auditLogs.commercial_history.map((h) => (
              <div key={h.ID} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <span className="satiro-badge bg-slate-100 text-slate-700 mr-2">
                    {h.ENTIDADE} • {h.ACAO}
                  </span>
                  <span className="text-slate-800 font-medium">{h.DESCRICAO}</span>
                </div>
                <span className="text-slate-400 font-mono">{h.DT_CRIA}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'password' && (
        <div className="satiro-card p-6 max-w-md space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Perfil Logado: {user?.NOME}</h3>
            <p className="text-xs text-slate-500">
              Login: {user?.LOGIN} • Perfil: {user?.PERFIL} • Alçada de Desconto: {user?.DESC_MAX}%
            </p>
          </div>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="satiro-label">Senha Atual *</label>
              <div className="relative">
                <input
                  required
                  type={showSecrets['currentPassword'] ? 'text' : 'password'}
                  value={pwdForm.current_password}
                  onChange={(e) => setPwdForm({ ...pwdForm, current_password: e.target.value })}
                  className="satiro-input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleSecret('currentPassword')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                  title={showSecrets['currentPassword'] ? 'Ocultar senha' : 'Exibir senha'}
                >
                  {showSecrets['currentPassword'] ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="satiro-label">Nova Senha *</label>
              <div className="relative">
                <input
                  required
                  type={showSecrets['newPassword'] ? 'text' : 'password'}
                  value={pwdForm.new_password}
                  onChange={(e) => setPwdForm({ ...pwdForm, new_password: e.target.value })}
                  className="satiro-input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleSecret('newPassword')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                  title={showSecrets['newPassword'] ? 'Ocultar senha' : 'Exibir senha'}
                >
                  {showSecrets['newPassword'] ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <button type="submit" className="satiro-btn-primary w-full justify-center">
              Atualizar Senha
            </button>
          </form>
        </div>
      )}
    </div>
  );
};


