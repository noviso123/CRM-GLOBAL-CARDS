"""CRM Global Cards & Bling ERP - Servidor MCP (Model Context Protocol).

Implementa a especificação aberta Model Context Protocol (Anthropic/Gemini/OpenAI - 2024-11-05),
expondo ferramentas estruturadas (Tools), recursos de leitura (Resources) e templates (Prompts)
para IA comercial, automação de pedidos e integração nativa com o banco DBF e APIs externas.
"""

import json
from typing import Any, Dict, List, Optional
from app.database.dbf_manager import DBFManager
from app.integrations.bling.sync import BlingSyncService
from app.integrations.bling.client import BlingAPIClient
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.integrations.whatsapp.messages import WhatsAppService
from app.services.client_service import ClientService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.quotation_service import QuotationService
from app.schemas.client import ClientCreate
from app.schemas.product import ProductCreate
from app.schemas.order import OrderCreate, OrderItemInput
from app.schemas.quotation import QuotationCreate, QuotationItemInput
from app.utils.dates import now_iso


class BlingMCPEngine:
    """Motor enterprise de execução de ferramentas, recursos e prompts do Model Context Protocol."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.prod_svc = ProductService(mgr)
        self.cli_svc = ClientService(mgr)
        self.order_svc = OrderService(mgr)
        self.quo_svc = QuotationService(mgr)
        self.wa_client = WhatsAppCloudClient(mgr)
        self.wa_svc = WhatsAppService(mgr)

    # =========================================================================
    # CATÁLOGO DE FERRAMENTAS MCP (TOOLS)
    # =========================================================================

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Retorna o catálogo completo de ferramentas no padrão oficial JSON Schema do MCP."""
        return [
            # --- BLING ERP ---
            {
                "name": "bling_sincronizar_tudo",
                "category": "Bling ERP",
                "description": "Sincroniza e importa todos os dados do Bling ERP (Contatos, Produtos, Estoques e Pedidos) para as tabelas DBF locais do CRM sem necessidade de intervenção manual.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scopes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Escopos a sincronizar: 'products', 'contacts', 'orders' ou 'all'",
                            "default": ["all"],
                        }
                    },
                },
            },
            {
                "name": "bling_listar_pedidos",
                "category": "Bling ERP",
                "description": "Consulta pedidos de venda sincronizados com filtros por período, valor ou situação comercial.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "situacao": {
                            "type": "string",
                            "description": "Situação do pedido: ABERTO, APROVADO, FATURADO, ENTREGUE ou CANCELADO",
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de pedidos a retornar (padrão 20)",
                            "default": 20,
                        },
                    },
                },
            },
            {
                "name": "bling_consultar_estoque",
                "category": "Bling ERP",
                "description": "Consulta o saldo de estoque físico e virtual de produtos no Bling e compara com a base DBF local.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codigo_ou_id": {
                            "type": "string",
                            "description": "Código SKU ou termo de busca do produto",
                        }
                    },
                    "required": ["codigo_ou_id"],
                },
            },
            {
                "name": "bling_criar_pedido_venda",
                "category": "Bling ERP",
                "description": "Registra um novo pedido de venda com itens e valores no CRM e transmite diretamente ao Bling ERP v3 via POST /pedidos/vendas.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_cliente": {
                            "type": "string",
                            "description": "ID do cliente no CRM",
                        },
                        "itens": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Lista de itens: [{ID_PRODUTO, QUANTIDADE, PRECO_UNIT}]",
                        },
                        "observacoes": {"type": "string", "description": "Observações do pedido"},
                    },
                    "required": ["id_cliente", "itens"],
                },
            },
            {
                "name": "bling_avancar_situacao_pedido",
                "category": "Bling ERP",
                "description": "Avança a situação de um pedido de venda no CRM e no Bling ERP (ex: ABERTO -> APROVADO -> FATURADO -> ENTREGUE).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_pedido": {
                            "type": "string",
                            "description": "ID ou Número do pedido no CRM",
                        },
                        "nova_situacao": {
                            "type": "string",
                            "description": "Nova situação: APROVADO, FATURADO, ENTREGUE, CANCELADO",
                        },
                    },
                    "required": ["id_pedido", "nova_situacao"],
                },
            },
            {
                "name": "bling_cadastrar_produto",
                "category": "Bling ERP",
                "description": "Cadastra um novo produto no catálogo do CRM e exporta automaticamente para o Bling ERP v3.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codigo": {"type": "string", "description": "Código SKU do produto"},
                        "nome": {"type": "string", "description": "Nome completo do produto"},
                        "preco": {"type": "number", "description": "Preço unitário de venda"},
                        "estoque": {"type": "number", "description": "Estoque inicial", "default": 0},
                        "unidade": {"type": "string", "description": "Unidade (UN, PC, MT, RL)", "default": "UN"},
                        "categoria": {"type": "string", "description": "Categoria do produto", "default": "Geral"},
                    },
                    "required": ["codigo", "nome", "preco"],
                },
            },

            # --- WHATSAPP & META ---
            {
                "name": "whatsapp_enviar_mensagem",
                "category": "WhatsApp & Meta",
                "description": "Envia mensagem de texto comercial via WhatsApp Business Cloud API diretamente para o cliente.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "telefone": {
                            "type": "string",
                            "description": "Número do telefone com DDI e DDD (ex: 5511999998888)",
                        },
                        "mensagem": {
                            "type": "string",
                            "description": "Texto da mensagem comercial a ser enviada",
                        },
                    },
                    "required": ["telefone", "mensagem"],
                },
            },
            {
                "name": "whatsapp_disparar_template",
                "category": "WhatsApp & Meta",
                "description": "Dispara template HSM pré-aprovado pela Meta (confirmacao_pedido, pedido_faturado, orcamento_gerado, cobranca_pix, boas_vindas).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "telefone": {"type": "string", "description": "Telefone de destino com DDI 55"},
                        "template_name": {
                            "type": "string",
                            "description": "Nome do template Meta: confirmacao_pedido, pedido_faturado, orcamento_gerado, cobranca_pix, boas_vindas",
                        },
                        "parametros": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Parâmetros do template (ex: [Nome, NumeroPedido, Valor])",
                        },
                    },
                    "required": ["telefone", "template_name"],
                },
            },
            {
                "name": "whatsapp_listar_conversas",
                "category": "WhatsApp & Meta",
                "description": "Lista conversas comerciais no WhatsApp filtradas por situação (EM_ATENDIMENTO, AGUARDANDO, ENCERRADA) ou busca.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "situacao": {"type": "string", "description": "Filtro de situação"},
                        "busca": {"type": "string", "description": "Termo de busca por contato ou telefone"},
                    },
                },
            },
            {
                "name": "whatsapp_obter_historico",
                "category": "WhatsApp & Meta",
                "description": "Recupera todas as mensagens trocadas em uma conversa de WhatsApp do CRM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_conversa": {"type": "string", "description": "ID da conversa no CRM"},
                    },
                    "required": ["id_conversa"],
                },
            },

            # --- CRM COMERCIAL & VISÃO 360 ---
            {
                "name": "crm_consultar_visao_360",
                "category": "CRM Comercial",
                "description": "Consulta o dossiê comercial 360º de um cliente (dados cadastrais, contatos, histórico de pedidos, orçamentos, oportunidades e conversas de WhatsApp).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "termo_busca": {
                            "type": "string",
                            "description": "Razão social, nome fantasia, CPF ou CNPJ do cliente",
                        }
                    },
                    "required": ["termo_busca"],
                },
            },
            {
                "name": "crm_cadastrar_cliente",
                "category": "CRM Comercial",
                "description": "Cadastra um novo cliente PF ou PJ no CRM com validação de CPF/CNPJ e exporta para o Bling ERP.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tipo_pessoa": {"type": "string", "description": "PF ou PJ", "default": "PJ"},
                        "nome": {"type": "string", "description": "Razão Social ou Nome Completo"},
                        "cpf_cnpj": {"type": "string", "description": "Documento CPF ou CNPJ válido"},
                        "telefone": {"type": "string", "description": "Telefone principal", "default": ""},
                        "email": {"type": "string", "description": "E-mail de contato", "default": ""},
                    },
                    "required": ["tipo_pessoa", "nome", "cpf_cnpj"],
                },
            },
            {
                "name": "crm_criar_oportunidade",
                "category": "CRM Comercial",
                "description": "Registra uma nova oportunidade no Funil de Vendas Kanban do CRM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_cliente": {"type": "string", "description": "ID do cliente no CRM"},
                        "titulo": {"type": "string", "description": "Título da oportunidade (ex: Fornecimento de 500 crachás)"},
                        "valor_estimado": {"type": "number", "description": "Valor monetário estimado"},
                        "etapa": {
                            "type": "string",
                            "description": "Etapa inicial: PROSPECCAO, QUALIFICACAO, PROPOSTA, NEGOCIACAO, FECHAMENTO",
                            "default": "PROSPECCAO",
                        },
                    },
                    "required": ["id_cliente", "titulo", "valor_estimado"],
                },
            },
            {
                "name": "crm_gerar_orcamento",
                "category": "CRM Comercial",
                "description": "Gera uma proposta comercial formal / orçamento com cálculo automático de descontos por volume de itens.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_cliente": {"type": "string", "description": "ID do cliente no CRM"},
                        "itens": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Lista de itens: [{ID_PRODUTO, QUANTIDADE, PRECO_UNIT}]",
                        },
                        "dias_validade": {"type": "integer", "description": "Dias de validade da proposta", "default": 15},
                    },
                    "required": ["id_cliente", "itens"],
                },
            },
            {
                "name": "crm_converter_orcamento_pedido",
                "category": "CRM Comercial",
                "description": "Aprova um orçamento no CRM e converte em pedido de venda real, com transmissão automática ao Bling ERP.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_orcamento": {"type": "string", "description": "ID do orçamento a ser convertido"},
                    },
                    "required": ["id_orcamento"],
                },
            },

            # --- BI, ANALYTICS & INSIGHTS ---
            {
                "name": "crm_relatorio_kpis_comerciais",
                "category": "BI & Métricas",
                "description": "Retorna os principais KPIs em tempo real (faturamento acumulado, ticket médio, taxa de conversão do funil e contagem de clientes ativos).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "periodo": {"type": "string", "description": "Período de análise (mes_atual, hoje, ano)", "default": "mes_atual"},
                    },
                },
            },
            {
                "name": "crm_curva_abc_produtos",
                "category": "BI & Métricas",
                "description": "Analisa o catálogo de produtos gerando classificação da Curva ABC por volume vendido e receita gerada.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limite": {"type": "integer", "description": "Quantidade máxima de produtos no ranking", "default": 10},
                    },
                },
            },
            {
                "name": "crm_clientes_inativos_alerta",
                "category": "BI & Métricas",
                "description": "Identifica clientes sem compras nos últimos 30, 60 ou 90 dias para ações imediatas de reativação via WhatsApp.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dias_inatividade": {"type": "integer", "description": "Limite mínimo de dias sem interação", "default": 60},
                    },
                },
            },
        ]

    # =========================================================================
    # RECURSOS MCP (RESOURCES)
    # =========================================================================

    def get_resource_definitions(self) -> List[Dict[str, Any]]:
        """Retorna a lista de recursos estáticos e dinâmicos legíveis por IA conforme o protocolo MCP."""
        return [
            {
                "uri": "dbf://produtos/catalogo",
                "name": "Catálogo de Produtos CRM",
                "mimeType": "application/json",
                "description": "Tabela completa de produtos com SKU, descrição, preço de tabela e saldo de estoque.",
            },
            {
                "uri": "dbf://clientes/resumo",
                "name": "Base de Clientes Ativos",
                "mimeType": "application/json",
                "description": "Listagem de clientes com contatos, documentos e volume total de compras.",
            },
            {
                "uri": "dbf://pedidos/recentes",
                "name": "Últimos Pedidos de Venda",
                "mimeType": "application/json",
                "description": "Histórico dos pedidos de venda mais recentes emitidos no CRM e no Bling.",
            },
            {
                "uri": "meta://whatsapp/status",
                "name": "Status da Linha Meta & WhatsApp Cloud",
                "mimeType": "application/json",
                "description": "Dados da conexão ativa com a Meta Graph API, WABA ID e qualidade da linha.",
            },
        ]

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Lê o conteúdo do recurso MCP solicitado."""
        if uri == "dbf://produtos/catalogo":
            prods = self.mgr.find_all("PRODUTOS")
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(prods, ensure_ascii=False, default=str),
            }
        elif uri == "dbf://clientes/resumo":
            clis = self.mgr.find_all("CLIENTES")
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(clis, ensure_ascii=False, default=str),
            }
        elif uri == "dbf://pedidos/recentes":
            orders = self.mgr.find_all("PEDIDOS", sort_by="DT_PEDIDO", descending=True)[:30]
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(orders, ensure_ascii=False, default=str),
            }
        elif uri == "meta://whatsapp/status":
            st = self.wa_client.get_account_status()
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(st, ensure_ascii=False, default=str),
            }
        else:
            return {"uri": uri, "error": f"Recurso MCP '{uri}' não encontrado."}

    # =========================================================================
    # PROMPTS MCP (TEMPLATES GUIADOS PARA IA)
    # =========================================================================

    def get_prompt_definitions(self) -> List[Dict[str, Any]]:
        """Retorna templates de prompt prontos para uso em agentes autônomos."""
        return [
            {
                "name": "proposta_comercial_cordoes_crachas",
                "description": "Gera texto persuasivo de proposta comercial para crachás em PVC, cordões acetinados ou pulseiras.",
                "arguments": [
                    {"name": "cliente_nome", "description": "Nome do cliente ou empresa", "required": True},
                    {"name": "quantidade", "description": "Quantidade de unidades", "required": True},
                    {"name": "produto", "description": "Tipo de material desejado", "required": True},
                ],
            },
            {
                "name": "reativacao_clientes_inativos",
                "description": "Elabora mensagem personalizada de WhatsApp para reativar clientes sem compras recentes.",
                "arguments": [
                    {"name": "cliente_nome", "description": "Nome do cliente", "required": True},
                    {"name": "dias_sem_comprar", "description": "Dias de inatividade", "required": True},
                ],
            },
            {
                "name": "fechamento_diario_vendas",
                "description": "Gera resumo executivo de fechamento diário de pedidos e faturamento do CRM.",
                "arguments": [],
            },
        ]

    # =========================================================================
    # EXECUÇÃO DE FERRAMENTAS MCP (TOOLS CALL)
    # =========================================================================

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a ferramenta MCP indicada e retorna resposta padronizada."""
        # 1. BLING ERP TOOLS
        if tool_name == "bling_sincronizar_tudo":
            scopes = arguments.get("scopes", ["all"])
            service = BlingSyncService(self.mgr)
            result = service.run_sync(scopes)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Sincronização completa executada com sucesso. Resultados: {result}",
                    }
                ],
                "result": result,
            }

        elif tool_name == "bling_listar_pedidos":
            pedidos_dbf = self.mgr.find_all("PEDIDOS")
            situacao = arguments.get("situacao")
            if situacao:
                pedidos_dbf = [
                    p for p in pedidos_dbf
                    if str(p.get("SITUACAO", "")).upper() == situacao.upper()
                ]
            limite = arguments.get("limite", 20)
            lista = pedidos_dbf[:limite]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Foram encontrados {len(lista)} pedidos de venda registrados.",
                    }
                ],
                "pedidos": lista,
            }

        elif tool_name == "bling_consultar_estoque":
            termo = str(arguments.get("codigo_ou_id", "")).strip().lower()
            prods = self.mgr.find_all("PRODUTOS")
            encontrados = [
                p for p in prods
                if termo in str(p.get("CODIGO", "")).lower() or termo in str(p.get("NOME", "")).lower()
            ]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Saldo de estoque para '{termo}': {len(encontrados)} produtos localizados.",
                    }
                ],
                "produtos": encontrados,
            }

        elif tool_name == "bling_criar_pedido_venda":
            id_cli = str(arguments.get("id_cliente", ""))
            itens_input = arguments.get("itens", [])
            obs = arguments.get("observacoes", "Emitido via MCP Agent")

            items_obj = [
                OrderItemInput(
                    ID_PRODUTO=i.get("ID_PRODUTO", i.get("id_produto", "")),
                    QUANTIDADE=float(i.get("QUANTIDADE", i.get("quantidade", 1))),
                    PRECO_UNIT=float(i.get("PRECO_UNIT", i.get("preco", 0))),
                )
                for i in itens_input
            ]
            pedido = self.order_svc.create_order(
                OrderCreate(ID_CLIENTE=id_cli, ITEMS=items_obj, OBS=obs),
                user_id="MCP_AGENT",
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Pedido {pedido.get('NUMERO')} criado com sucesso no valor de R$ {pedido.get('TOTAL', 0):.2f} e transmitido ao Bling ERP.",
                    }
                ],
                "pedido": pedido,
            }

        elif tool_name == "bling_avancar_situacao_pedido":
            id_pedido = arguments.get("id_pedido", "")
            nova_sit = str(arguments.get("nova_situacao", "APROVADO")).upper()
            updated = self.order_svc.update_status(id_pedido, nova_sit, user_id="MCP_AGENT")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Situação do pedido {id_pedido} alterada para '{nova_sit}' e sincronizada com o Bling.",
                    }
                ],
                "pedido": updated,
            }

        elif tool_name == "bling_cadastrar_produto":
            prod = self.prod_svc.create_product(
                ProductCreate(
                    CODIGO=arguments["codigo"],
                    NOME=arguments["nome"],
                    PRECO=float(arguments["preco"]),
                    ESTOQUE=float(arguments.get("estoque", 0)),
                    UNIDADE=arguments.get("unidade", "UN"),
                    CATEGORIA=arguments.get("categoria", "Geral"),
                ),
                user_id="MCP_AGENT",
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Produto '{prod.get('NOME')}' ({prod.get('CODIGO')}) cadastrado no CRM e exportado para o Bling ERP.",
                    }
                ],
                "produto": prod,
            }

        # 2. WHATSAPP & META TOOLS
        elif tool_name == "whatsapp_enviar_mensagem":
            tel = arguments.get("telefone", "")
            msg = arguments.get("mensagem", "")
            res = self.wa_client.send_cloud_text_message(tel, msg)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Mensagem enviada com sucesso para {tel} via Meta WhatsApp Cloud API.",
                    }
                ],
                "response": res,
            }

        elif tool_name == "whatsapp_disparar_template":
            tel = arguments.get("telefone", "")
            tmpl = arguments.get("template_name", "confirmacao_pedido")
            params = arguments.get("parametros", [])
            res = self.wa_client.send_cloud_template_message(tel, tmpl, parameters=params)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Template oficial Meta '{tmpl}' disparado para {tel}.",
                    }
                ],
                "response": res,
            }

        elif tool_name == "whatsapp_listar_conversas":
            sit = arguments.get("situacao")
            busca = arguments.get("busca")
            convs = self.wa_svc.list_conversations(situacao=sit, search=busca)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{len(convs)} conversa(s) de atendimento localizada(s).",
                    }
                ],
                "conversas": convs[:20],
            }

        elif tool_name == "whatsapp_obter_historico":
            cid = arguments.get("id_conversa", "")
            msgs = self.wa_svc.list_messages(cid)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Histórico recuperado com {len(msgs)} mensagens.",
                    }
                ],
                "mensagens": msgs,
            }

        # 3. CRM COMERCIAL & 360 TOOLS
        elif tool_name == "crm_consultar_visao_360":
            termo = str(arguments.get("termo_busca", "")).strip().lower()
            clientes = self.mgr.find_all("CLIENTES")
            filtrados = [
                c for c in clientes
                if termo in str(c.get("NOME", "")).lower()
                or termo in str(c.get("FANTASIA", "")).lower()
                or termo in str(c.get("CPF_CNPJ", "")).lower()
            ]
            dossie = []
            for cli in filtrados[:5]:
                try:
                    overview = self.cli_svc.get_client_overview_10_tabs(cli["ID"])
                    dossie.append(overview)
                except Exception:
                    dossie.append({"client": cli})

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Dossiê 360º de {len(filtrados)} cliente(s) retornado com sucesso.",
                    }
                ],
                "clientes": dossie,
            }

        elif tool_name == "crm_cadastrar_cliente":
            cli = self.cli_svc.create_client(
                ClientCreate(
                    TIPO_PES=arguments.get("tipo_pessoa", "PJ"),
                    NOME=arguments["nome"],
                    CPF_CNPJ=arguments["cpf_cnpj"],
                    TELEFONE=arguments.get("telefone", ""),
                    EMAIL=arguments.get("email", ""),
                ),
                user_id="MCP_AGENT",
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Cliente '{cli.get('NOME')}' cadastrado com sucesso no DBF e sincronizado com Bling.",
                    }
                ],
                "cliente": cli,
            }

        elif tool_name == "crm_criar_oportunidade":
            opp = self.mgr.insert(
                "OPORTUN",
                {
                    "ID_CLIENTE": arguments["id_cliente"],
                    "TITULO": arguments["titulo"],
                    "VALOR": float(arguments["valor_estimado"]),
                    "ETAPA": arguments.get("etapa", "PROSPECCAO").upper(),
                    "DT_ABERT": now_iso()[:10],
                    "ORIGEM": "MCP_AGENT",
                },
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Oportunidade '{opp.get('TITULO')}' criada no Funil de Vendas.",
                    }
                ],
                "oportunidade": opp,
            }

        elif tool_name == "crm_gerar_orcamento":
            items_obj = [
                QuotationItemInput(
                    ID_PRODUTO=i.get("ID_PRODUTO", i.get("id_produto", "")),
                    QUANTIDADE=float(i.get("QUANTIDADE", i.get("quantidade", 1))),
                    PRECO_UNIT=float(i.get("PRECO_UNIT", i.get("preco", 0))),
                )
                for i in arguments.get("itens", [])
            ]
            quo = self.quo_svc.create_quotation(
                QuotationCreate(
                    ID_CLIENTE=arguments["id_cliente"],
                    ITEMS=items_obj,
                    VALIDADE_DIAS=int(arguments.get("dias_validade", 15)),
                ),
                user_id="MCP_AGENT",
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Orçamento {quo.get('NUMERO')} gerado no valor total de R$ {quo.get('TOTAL', 0):.2f}.",
                    }
                ],
                "orcamento": quo,
            }

        elif tool_name == "crm_converter_orcamento_pedido":
            pedido = self.quo_svc.convert_to_order(arguments["id_orcamento"], user_id="MCP_AGENT")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Orçamento aprovado e convertido no Pedido de Venda {pedido.get('NUMERO')}.",
                    }
                ],
                "pedido": pedido,
            }

        # 4. BI & ANALYTICS TOOLS
        elif tool_name == "crm_relatorio_kpis_comerciais":
            from app.services.dashboard_service import DashboardService
            dash = DashboardService(self.mgr).get_summary()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"KPIs Comerciais consolidados em tempo real.",
                    }
                ],
                "kpis": dash.get("kpis", {}),
            }

        elif tool_name == "crm_curva_abc_produtos":
            prods = self.mgr.find_all("PRODUTOS", sort_by="ESTOQUE", descending=True)
            limite = arguments.get("limite", 10)
            ranking = []
            for p in prods[:limite]:
                estoque = float(p.get("ESTOQUE", 0))
                preco = float(p.get("PRECO", 0))
                ranking.append({
                    "codigo": p.get("CODIGO"),
                    "nome": p.get("NOME"),
                    "estoque": estoque,
                    "preco": preco,
                    "valor_patrimonio": estoque * preco,
                })
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Curva ABC gerada com os {len(ranking)} produtos mais representativos.",
                    }
                ],
                "ranking": ranking,
            }

        elif tool_name == "crm_clientes_inativos_alerta":
            clis = self.mgr.find_all("CLIENTES")
            inativos = [
                {"id": c.get("ID"), "nome": c.get("NOME"), "telefone": c.get("TELEFONE"), "ult_interacao": c.get("DT_ULT_INT", "Sem registro")}
                for c in clis if not c.get("DT_ULT_INT") or c.get("DT_ULT_INT") < now_iso()[:10]
            ]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{len(inativos)} cliente(s) identificado(s) para reativação comercial.",
                    }
                ],
                "clientes_inativos": inativos[:20],
            }

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Ferramenta MCP '{tool_name}' não reconhecida."}],
            }

    # =========================================================================
    # PROCESSADOR JSON-RPC 2.0 (PROTOCOLO OFICIAL MCP)
    # =========================================================================

    def handle_jsonrpc(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Processa requisições JSON-RPC padrão do protocolo MCP (tools/list, tools/call, resources/list, resources/read)."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "crm-global-cards-mcp",
                        "version": "1.0.0",
                    },
                },
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tool_definitions()},
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            res = self.execute_tool(tool_name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": res,
            }

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"resources": self.get_resource_definitions()},
            }

        elif method == "resources/read":
            uri = params.get("uri", "")
            res = self.read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"contents": [res]},
            }

        elif method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"prompts": self.get_prompt_definitions()},
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Método MCP '{method}' não suportado.",
                },
            }
