from typing import List
from app.database.dbf_manager import DBFManager

MODULES_LIST: List[str] = [
    "DASHBOARD",
    "CLIENTES",
    "CONTATOS",
    "PRODUTOS",
    "PEDIDOS",
    "ORCAMENTOS",
    "OPORTUNIDADES",
    "FUNIL",
    "ATIVIDADES",
    "WHATSAPP",
    "NOTIFICACOES",
    "INTEGRACOES",
    "IA",
    "RELATORIOS",
    "CONFIGURACOES",
]


def run_startup_migrations(mgr: DBFManager, hash_password_fn) -> None:
    """Inicializa os 21 arquivos DBF e garante apenas a configuração estrutural mínima (sem dados comerciais fictícios)."""
    mgr.initialize_all_tables()

    # 1. Garantir Usuário Administrador Inicial caso a tabela USUARIOS esteja vazia
    users = mgr.find_all("USUARIOS")
    if not users:
        mgr.insert(
            "USUARIOS",
            {
                "NOME": "Administrador GLOBAL CARDS",
                "LOGIN": "admin",
                "EMAIL": "admin@globalcards.com.br",
                "SENHA_HASH": hash_password_fn("GlobalCards@2026"),
                "PERFIL": "ADMIN",
                "CARGO": "Administrador Geral",
                "TELEFONE": "",
                "DESC_MAX": 100.0,
                "TENT_INV": 0,
                "SITUACAO": "ATIVO",
            },
        )

    # 2. Garantir matriz de permissões por perfil
    perms = mgr.find_all("PERMISSO")
    if not perms:
        profiles = {
            "ADMIN": (True, True, True, True, True),
            "GERENTE": (True, True, True, True, True),
            "VENDEDOR": (True, True, True, False, True),
            "ATENDIMENTO": (True, True, True, False, False),
        }
        for prof, (ver, criar, editar, excluir, export) in profiles.items():
            for mod in MODULES_LIST:
                mgr.insert(
                    "PERMISSO",
                    {
                        "PERFIL": prof,
                        "MODULO": mod,
                        "P_VER": ver if not (prof in ("VENDEDOR", "ATENDIMENTO") and mod == "CONFIGURACOES") else True,
                        "P_CRIAR": criar if mod != "CONFIGURACOES" or prof == "ADMIN" else False,
                        "P_EDITAR": editar if mod != "CONFIGURACOES" or prof == "ADMIN" else False,
                        "P_EXCLUIR": excluir if mod != "CONFIGURACOES" or prof == "ADMIN" else False,
                        "P_EXPORT": export,
                    },
                )

    # 3. Garantir Funil Comercial Padrão e as 8 Etapas configuráveis iniciais (sem oportunidades fictícias)
    funnels = mgr.find_all("FUNIL")
    if not funnels:
        default_funnel = mgr.insert(
            "FUNIL",
            {
                "NOME": "Funil Comercial Principal",
                "DESCRICAO": "Pipeline padrão de vendas B2B e identificação corporativa",
                "PADRAO": True,
                "SITUACAO": "ATIVO",
            },
        )
        default_stages = [
            ("Novo contato", 1, "#64748B", 10.0, "ABERTA"),
            ("Qualificação", 2, "#0284C7", 25.0, "ABERTA"),
            ("Primeiro atendimento", 3, "#0EA5E9", 40.0, "ABERTA"),
            ("Proposta enviada", 4, "#2563EB", 60.0, "ABERTA"),
            ("Negociação", 5, "#D97706", 75.0, "ABERTA"),
            ("Aguardando aprovação", 6, "#7C3AED", 90.0, "ABERTA"),
            ("Venda ganha", 7, "#16A34A", 100.0, "GANHA"),
            ("Venda perdida", 8, "#DC2626", 0.0, "PERDIDA"),
        ]
        for nome, ordem, cor, prob, tipo in default_stages:
            mgr.insert(
                "ETAPAS",
                {
                    "ID_FUNIL": default_funnel["ID"],
                    "NOME": nome,
                    "ORDEM": ordem,
                    "COR": cor,
                    "PROB_PAD": prob,
                    "TIPO_ETAPA": tipo,
                    "SITUACAO": "ATIVO",
                },
            )

    # 4. Garantir registros de configuração dos provedores de integração em INTEGR.DBF
    integrations = mgr.find_all("INTEGR")
    existing_providers = {i["PROVEDOR"] for i in integrations}
    for prov in ("BLING", "WHATSAPP", "META", "IA_PROVIDER"):
        if prov not in existing_providers:
            mgr.insert(
                "INTEGR",
                {
                    "PROVEDOR": prov,
                    "SITUACAO": "DESCONECTADO",
                    "STATUS_MSG": "Aguardando configuração de credenciais.",
                    "TOTAL_SYNC": 0,
                },
            )

    # 5. Garantir configurações padrão em CONFIG.DBF
    configs = mgr.find_all("CONFIG")
    existing_keys = {c["CHAVE"] for c in configs}
    default_configs = [
        ("EMPRESA", "NOME_EMPRESA", "CRM GLOBAL CARDS — Gestão Comercial", "Nome exibido no cabeçalho e relatórios"),
        ("VISUAL", "COR_PRIMARIA", "#0F3D6E", "Cor primária do Design System"),
        ("COMERCIAL", "DESCONTO_MAX_SEM_APROVACAO", "10.0", "Percentual máximo de desconto padrão sem alçada de gerência"),
        ("COMERCIAL", "VALIDADE_PADRAO_ORCAMENTO_DIAS", "15", "Prazo padrão de validade de novos orçamentos"),
        ("BACKUP", "BACKUP_RETENCAO_DIAS", "30", "Quantidade de dias para retenção de backups locais"),
        ("BACKUP", "BACKUP_AUTOMATICO_ATIVO", "true", "Realizar backup consistente automaticamente"),
    ]
    for grupo, chave, valor, desc in default_configs:
        if chave not in existing_keys:
            mgr.insert(
                "CONFIG",
                {
                    "GRUPO": grupo,
                    "CHAVE": chave,
                    "VALOR": valor,
                    "DESCRICAO": desc,
                },
            )

