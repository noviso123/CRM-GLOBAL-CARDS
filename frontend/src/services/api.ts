const API_BASE = 'http://127.0.0.1:8765/api';

export function getStoredToken(): string | null {
  return localStorage.getItem('satiro_crm_token');
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem('satiro_crm_token', token);
  } else {
    localStorage.removeItem('satiro_crm_token');
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `Erro HTTP ${response.status}`;
    try {
      const errBody = await response.json();
      errorMessage = errBody.message || errBody.detail || errorMessage;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

export async function downloadAuthorizedCsv(endpoint: string, filename: string): Promise<void> {
  const token = getStoredToken();
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new Error('Não foi possível exportar o arquivo CSV.');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

