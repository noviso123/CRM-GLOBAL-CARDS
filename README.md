# CRM GLOBAL CARDS + Bling

[![Licença Comercial](https://img.shields.io/badge/licen%C3%A7a-comercial%20paga-red.svg)](LICENSE)
[![Status](https://img.shields.io/badge/versao-1.0.0-blue.svg)](https://github.com/noviso123/CRM-GLOBAL-CARDS)
[![Plataforma](https://img.shields.io/badge/plataforma-100%25%20local%20127.0.0.1-emerald.svg)](README.md)

> **AVISO DE LICENCIAMENTO COMERCIAL PAGO:**  
> Este software é proprietário e protegido por direitos autorais. O uso, instalação ou implantação comercial deste sistema **requer a aquisição prévia de uma Licença Comercial Paga**. Para adquirir sua licença de uso, consulte o arquivo [`LICENSE`](LICENSE) ou entre em contato com a equipe comercial.

Plataforma completa e independente de Gestão Comercial B2B/B2C, Catálogo de Produtos Global Cards, Funil de Vendas Kanban, Orçamentos, Pedidos, Atendimento WhatsApp e Integração Bidirecional Controlada com **Bling API v3**, operando **100% localmente (`127.0.0.1`)** sobre banco de dados nativo **dBase III+ (`.DBF`)** com **Zero SQL**.

---

## Arquitetura Resumida

- **Frontend (`frontend/`)**: TypeScript + React 18 + Vite + Tailwind CSS + Lucide Icons + Design System centralizado (`globals.css` e `tailwind.config.js`).
- **Backend (`backend/`)**: Python 3.12 + FastAPI + Pydantic v2 + Segurança JWT/Bcrypt/Fernet + Arquitetura modular por domínio.
- **Banco de Dados (`data/dbf/`)**: Motor binário nativo **`GlobalCardsDBFEngine`** (`0x03` dBase III+, codificação `CP1252`, índices secundários `.IDX` com `CRC32`, bloqueio concorrente `RLock + FileLock`, deleção lógica `0x2A` e compactação física `PACK`).
- **Restrição Zero-SQL Cumprida**: Nenhuma dependência de PostgreSQL, MySQL, SQL Server, SQLite, MariaDB, SQLAlchemy ou Alembic.

---

## Como Executar Localmente (`127.0.0.1`)

### Opção 1: Script Automatizado PowerShell
```powershell
.\scripts\start_crm.ps1
```

### Opção 2: Inicialização Manual

1. **Backend FastAPI (`http://127.0.0.1:8765`)**:
```powershell
cd backend
python run.py
```
- Documentação interativa OpenAPI/Swagger: `http://127.0.0.1:8765/docs`
- Credenciais administrativas iniciais criadas no primeiro boot:
  - **Usuário**: `admin`
  - **Senha**: `GlobalCards@2026`

2. **Frontend React + Vite (`http://127.0.0.1:5173`)**:
```powershell
cd frontend
npm install
npm run dev
```

---

## Como Executar a Suíte de Testes Automatizados

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Consulte o manual técnico detalhado em [`documentation/MANUAL_COMPLETO_CRM_GLOBAL_CARDS.md`](documentation/MANUAL_COMPLETO_CRM_GLOBAL_CARDS.md).

---

## Licenciamento Comercial & Termos

Este projeto é regido por uma **Licença Proprietária Comercial Paga**. Todos os direitos reservados a Noviso / Global Cards (2026).
Para termos completos, consulte o arquivo [`LICENSE`](LICENSE).

