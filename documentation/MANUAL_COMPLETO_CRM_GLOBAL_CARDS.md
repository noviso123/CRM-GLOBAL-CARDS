# MANUAL TÉCNICO E OPERACIONAL COMPLETO — CRM GLOBAL CARDS + BLING

Este documento contempla todos os **15 tópicos obrigatórios da Seção 35** do **CRM GLOBAL CARDS + Bling**.

---

## 1. Arquitetura do Sistema

O **CRM GLOBAL CARDS** foi projetado em arquitetura desacoplada de três camadas locais executadas exclusivamente em `127.0.0.1`:

1. **Camada de Apresentação (`frontend/`)**:
   - SPA em **React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons**.
   - Design System centralizado inspirado na experiência de catálogo B2B e hierarquia visual da Global Cards (`https://www.globalcards.com.br/`).
   - Comunicação exclusiva via API REST autenticada (`http://127.0.0.1:8765/api`). O frontend jamais acessa arquivos `.DBF` diretamente.
2. **Camada de Aplicação e Domínio (`backend/app/`)**:
   - **FastAPI + Pydantic v2** organizado em `core/`, `database/`, `schemas/`, `services/`, `integrations/`, `agents/` e `api/routes/`.
   - Autenticação JWT (`HS256`), hash de senhas `bcrypt`, criptografia `Fernet (AES-128-CBC + HMAC-SHA256)` para segredos de APIs externas e controle de acesso baseado em perfil e módulo (RBAC).
3. **Camada de Persistência Nativa (`GlobalCardsDBFEngine` em `data/dbf/`)**:
   - Armazenamento principal 100% em arquivos binários **dBase III+ (`.DBF`, assinatura `0x03`)**.
   - **Zero SQL**: sem SQLite, PostgreSQL, MySQL, SQL Server, MariaDB, SQLAlchemy ou Alembic.

---

## 2. Instalação

### Pré-requisitos
- **Sistema Operacional**: Windows 10/11 (ou Linux/macOS compatível).
- **Python**: `3.11+` (homologado em `3.12.10`).
- **Node.js**: `20+` (homologado em `v24.21.0`).

### Instalação de Dependências
```powershell
# 1. Dependências do Backend Python
pip install -r backend/requirements.txt

# 2. Dependências do Frontend TypeScript
cd frontend
npm install
```

---

## 3. Execução

- **Backend**:
  ```powershell
  python backend/run.py
  ```
  Escuta em `http://127.0.0.1:8765`. Na primeira execução, cria automaticamente as 21 tabelas `.DBF`, os índices `.IDX`, as etapas padrão do funil comercial, as categorias iniciais e o usuário `admin` (senha inicial: `GlobalCards@2026`).
- **Frontend**:
  ```powershell
  npm --prefix frontend run dev
  ```
  Escuta em `http://127.0.0.1:5173`.

---

## 4. Configuração

As configurações ficam em `backend/app/core/config.py`:
- Host local padrão: `127.0.0.1`
- Porta da API REST: `8765`
- Expiração da sessão JWT em minutos: `480` (8h)

---

## 5. Estrutura dos Arquivos DBF

Cada tabela reside em `data/dbf/<NOME>.DBF` seguindo rigorosamente a especificação binária **dBase III+ (`0x03`)**:
- **Cabeçalho (32 bytes)**:
  - Byte `0`: `0x03` (dBase III+ sem memo `.DBT`).
  - Bytes `1–3`: Data da última atualização (`AA MM DD`).
  - Bytes `4–7`: Total de registros físicos (`uint32 little-endian`).
  - Bytes `8–9`: Tamanho do cabeçalho em bytes (`uint16 little-endian`).
  - Bytes `10–11`: Tamanho de cada registro em bytes (`uint16 little-endian`).
  - Byte `14`: Flag de transação incompleta (`0x01` durante escrita, `0x00` após conclusão).
  - Byte `29`: Language driver `0x57` (`Windows ANSI CP1252`).
- **Descritores de Campos (`32 bytes` por campo)** seguidos pelo terminador `0x0D`.
- **Registros de Dados**:
  - Primeiro byte: `0x20` (Ativo) ou `0x2A` (`*` Deletado logicamente).
- **Terminador de Arquivo**: `0x1A` (`EOF`).

---

## 6. Dicionário de Dados (21 Tabelas `.DBF`)

| # | Arquivo `.DBF` | Entidade | Chave Primária | Principais Campos |
|---|---|---|---|---|
| 1 | `CLIENTES.DBF` | Clientes PF/PJ | `ID C(36)` | `CODIGO`, `TIPO_PES`, `NOME`, `FANTASIA`, `CPF_CNPJ`, `EMAIL`, `TELEFONE`, `CIDADE`, `UF`, `SITUACAO`, `ORIGEM`, `ID_EXT` |
| 2 | `CONTATOS.DBF` | Contatos de Clientes | `ID C(36)` | `ID_CLIENTE`, `NOME`, `CARGO`, `DEPTO`, `TELEFONE`, `CELULAR`, `EMAIL`, `PRINCIPAL` |
| 3 | `ENDERECOS.DBF` | Endereços Adicionais | `ID C(36)` | `ID_CLIENTE`, `TIPO_END`, `ENDERECO`, `NUMERO`, `BAIRRO`, `CIDADE`, `UF`, `CEP` |
| 4 | `CATEGORIAS.DBF` | Categorias do Catálogo | `ID C(36)` | `CODIGO`, `NOME`, `ID_PAI`, `ORDEM`, `ICONE`, `SITUACAO` |
| 5 | `PRODUTOS.DBF` | Catálogo de Produtos | `ID C(36)` | `CODIGO`, `NOME`, `DESC_CURTA`, `ID_CATEG`, `UNIDADE`, `PRECO`, `PRECO_CUST`, `DESC_MAX`, `ESTOQUE`, `EST_MIN`, `DESTAQUE`, `ID_EXT` |
| 6 | `PEDIDOS.DBF` | Cabeçalho de Pedidos | `ID C(36)` | `NUMERO`, `ID_CLIENTE`, `ID_ORCAM`, `ID_OPORT`, `DT_PEDIDO`, `SUBTOTAL`, `DESCONTO`, `FRETE`, `TOTAL`, `SITUACAO`, `ORIGEM`, `ID_EXT` |
| 7 | `ITENS_PED.DBF` | Itens de Pedido | `ID C(36)` | `ID_PEDIDO`, `ID_PRODUTO`, `CODIGO_PRD`, `NOME_PRD`, `QUANTIDADE`, `PRECO_UNIT`, `DESC_VALOR`, `SUBTOTAL` |
| 8 | `ORCAMENT.DBF` | Cabeçalho de Orçamentos | `ID C(36)` | `NUMERO`, `ID_CLIENTE`, `ID_OPORT`, `DT_EMISSAO`, `DT_VALID`, `SUBTOTAL`, `DESCONTO`, `DESC_PERC`, `FRETE`, `TOTAL`, `AUT_DESC`, `ID_PED_GER`, `SITUACAO` |
| 9 | `ITENS_ORC.DBF` | Itens de Orçamento | `ID C(36)` | `ID_ORCAM`, `ID_PRODUTO`, `CODIGO_PRD`, `NOME_PRD`, `QUANTIDADE`, `PRECO_UNIT`, `DESC_VALOR`, `SUBTOTAL` |
| 10 | `FUNIL.DBF` | Funis Comerciais | `ID C(36)` | `NOME`, `DESCRICAO`, `PADRAO`, `SITUACAO` |
| 11 | `ETAPAS.DBF` | Etapas do Funil | `ID C(36)` | `ID_FUNIL`, `NOME`, `ORDEM`, `COR`, `PROB_PAD`, `TIPO_ETAPA` |
| 12 | `OPORTUN.DBF` | Oportunidades | `ID C(36)` | `TITULO`, `ID_CLIENTE`, `ID_CONTATO`, `ID_FUNIL`, `ID_ETAPA`, `VALOR_EST`, `PROBABIL`, `DT_PREV`, `MOT_PERDA`, `SITUACAO` |
| 13 | `ATIVIDAD.DBF` | Atividades e Tarefas | `ID C(36)` | `TITULO`, `DESCRICAO`, `TIPO`, `ID_CLIENTE`, `ID_OPORT`, `DATA_AG`, `HORA_AG`, `DT_PRAZO`, `DT_CONCL`, `PRIORIDADE`, `SITUACAO` |
| 14 | `HISTORIC.DBF` | Histórico Comercial | `ID C(36)` | `ENTIDADE`, `ID_REG`, `ID_CLIENTE`, `ACAO`, `DESCRICAO`, `ID_USUARIO`, `DT_CRIA` |
| 15 | `USUARIOS.DBF` | Usuários do Sistema | `ID C(36)` | `NOME`, `LOGIN`, `EMAIL`, `SENHA_HASH`, `PERFIL`, `CARGO`, `DESC_MAX`, `TENT_INV`, `BLOQ_ATE`, `SITUACAO` |
| 16 | `PERMISSO.DBF` | Matriz RBAC | `ID C(36)` | `PERFIL`, `MODULO`, `P_VER`, `P_CRIAR`, `P_EDITAR`, `P_EXCLUIR`, `P_EXPORT` |
| 17 | `NOTIFIC.DBF` | Notificações | `ID C(36)` | `ID_USU_DST`, `TIPO`, `TITULO`, `MENSAGEM`, `ENTIDADE`, `ID_REF`, `LIDA`, `DT_LEITURA` |
| 18 | `CONVERS.DBF` | Conversas WhatsApp | `ID C(36)` | `TELEFONE`, `NOME_CONT`, `ID_CLIENTE`, `ID_CONTATO`, `ID_OPORT`, `ULT_MSG`, `NAO_LIDAS`, `SITUACAO` |
| 19 | `MENSAGEN.DBF` | Mensagens WhatsApp | `ID C(36)` | `ID_CONVERS`, `ID_MSG_EXT`, `DIRECAO`, `TIPO_MSG`, `CONTEUDO`, `STATUS_ENT`, `DT_ENVIO` |
| 20 | `INTEGR.DBF` | Status de Integrações | `ID C(36)` | `PROVEDOR`, `SITUACAO`, `CLIENT_ID`, `CRED_REF`, `EXPIRA_EM`, `ULT_SYNC`, `STATUS_MSG`, `TOTAL_SYNC` |
| 21 | `CONFIG.DBF` | Parâmetros Globais | `ID C(36)` | `GRUPO`, `CHAVE`, `VALOR`, `DESCRICAO`, `ID_USUARIO`, `DT_ATUA` |

---

## 7. Índices Secundários (`.IDX`)

Para evitar varredura linear (`full scan`) em buscas frequentes, cada tabela `<TABELA>.DBF` possui um arquivo `<TABELA>.IDX` contendo:
- `primary`: mapa `ID -> record_number (0-based)` para leitura posicional `O(1)` via `f.seek()`.
- `secondary`: índices invertidos para chaves de negócio (`CPF_CNPJ`, `CODIGO`, `NUMERO`, `ID_CLIENTE`, `ID_EXT`, `LOGIN`, `TELEFONE`).
- `crc32`: checksum de verificação automática; se o `.IDX` estiver ausente ou divergente, é reconstruído automaticamente a partir do `.DBF`.

---

## 8. Relacionamentos e Integridade Referencial

Gerenciados por `backend/app/database/integrity.py`:
- **Bloqueio de Exclusão**: um registro de `CLIENTES.DBF` não pode ser excluído se possuir registros ativos vinculados em `PEDIDOS.DBF`, `ORCAMENT.DBF` ou `OPORTUN.DBF`.
- **Prevenção de Duplicidade**: validação de `CPF_CNPJ` único em `CLIENTES`, `CODIGO` único em `PRODUTOS` e `LOGIN` único em `USUARIOS`.

---

## 9. Endpoints da API REST

- `/api/auth`: `POST /login`, `POST /logout`, `GET /me`, `POST /change-password`, `POST /recover-password`
- `/api/dashboard`: `GET /summary`
- `/api/clients`: `GET /`, `POST /`, `GET /export/csv`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `GET /{id}/overview`, `POST /{id}/addresses`, `POST /{id}/notes`
- `/api/contacts`: `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`
- `/api/products`: `GET /`, `POST /`, `GET /categories`, `POST /categories`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`
- `/api/orders`: `GET /`, `POST /`, `GET /export/csv`, `GET /{id}`, `PATCH /{id}/status`, `DELETE /{id}`
- `/api/quotations`: `GET /`, `POST /`, `GET /{id}`, `PATCH /{id}/status`, `POST /{id}/duplicate`, `POST /{id}/convert-to-order`, `DELETE /{id}`
- `/api/opportunities`: `GET /funnels`, `GET /`, `POST /`, `GET /{id}`, `PUT /{id}`, `PATCH /{id}/stage`, `DELETE /{id}`
- `/api/activities`: `GET /`, `POST /`, `PUT /{id}`, `PATCH /{id}/complete`, `DELETE /{id}`
- `/api/whatsapp`: `GET /conversations`, `POST /conversations`, `PATCH /conversations/{id}/link`, `GET /conversations/{id}/messages`, `POST /conversations/{id}/messages`, `POST /webhook`
- `/api/notifications`: `GET /`, `PATCH /{id}/read`, `POST /read-all`
- `/api/reports`: `GET /{report_type}`, `GET /{report_type}/csv`
- `/api/integrations`: `GET /status`, `POST /bling/config`, `GET /bling/oauth/authorize-url`, `GET /bling/oauth/callback`, `POST /bling/sync`, `POST /bling/webhook`, `POST /whatsapp/config`, `POST /meta/config`
- `/api/settings`: `GET /`, `PUT /`, `GET /users`, `POST /users`, `PUT /users/{id}`, `GET /permissions`, `PUT /permissions`, `GET /backup/list`, `POST /backup/create`, `POST /backup/restore`, `GET /diagnostics/verify-dbf`, `POST /diagnostics/rebuild-indexes`, `GET /audit-logs`
- `/api/search`: `GET /?q=...`
- `/api/ai`: `POST /chat`

---

## 10. Integrações (Bling API v3, WhatsApp e Meta)

- **Propriedade dos Dados (Seção 17.3)**:
  - Quando `BlingSyncService` sincroniza produtos e clientes do Bling (`ORIGEM = "BLING"`), os campos internos exclusivos do CRM — como `DESC_MAX`, `DESTAQUE`, `EST_MIN`, `OBS_CURTA`, `DOC_REF` e `ID_RESP` — **nunca são sobrescritos**.
- **Independência Offline**:
  - Se o Bling ou a internet estiverem indisponíveis, todas as funcionalidades internas do CRM continuam operando normalmente sobre `data/dbf/`.

---

## 11. Procedimentos de Backup

Executados via tela **Configurações > Backups & Restauração ZIP** ou `POST /api/settings/backup/create`:
1. Adquire lock global sobre todas as 21 tabelas `.DBF`.
2. Gera pacote `.ZIP` em `data/backups/` contendo todos os `.DBF`, `.IDX`, `data/documents/` e um `manifest.json` com hash `SHA-256` de cada arquivo.

---

## 12. Procedimentos de Recuperação

- **Restauração de Backup**: `POST /api/settings/backup/restore` valida os hashes `SHA-256` do `manifest.json`, cria um backup preventivo do estado atual, extrai os arquivos `.DBF` e reconstrói todos os `.IDX`.
- **Reconstrução de Índices**: `POST /api/settings/diagnostics/rebuild-indexes` recria os 21 arquivos `.IDX` a partir da leitura física dos `.DBF`.
- **Recuperação de Escrita Incompleta**: no boot, `DBFTableConnection` verifica o Byte 14 do cabeçalho e trunca bytes residuais além de `header_size + num_records * record_size`.

---

## 13. Execução dos Testes

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 14. Manutenção da Base DBF

- **Compactação Física (`PACK`)**: registros excluídos recebem flag `0x2A` (`*`). O método `mgr.pack_table(table_name)` remove fisicamente os registros marcados via arquivo temporário `.TMP` e substituição atômica `os.replace()`.
- **Migração de Schema**: `SchemaMigrator.migrate_table()` em `backend/app/database/migrations.py` permite adicionar novas colunas preservando 100% dos registros existentes com backup prévio automático.

---

## 15. Solução de Problemas Comuns (Troubleshooting)

- **Erro `401 Sessão expirada ou inválida`**: faça login novamente em `/login` para renovar o token JWT.
- **Erro `423 Conta temporariamente bloqueada`**: ocorre após 5 tentativas seguidas de senha incorreta; aguarde 15 minutos ou peça a um administrador para redefinir a senha em **Configurações > Usuários**.
- **Divergência em busca rápida**: acesse **Configurações > Diagnóstico Motor DBF** e clique em **Reindexar Todas as 21 Tabelas (.IDX)**.

