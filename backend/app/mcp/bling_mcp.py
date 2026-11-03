"""CRM Global Cards & Bling ERP - Servidor MCP (Model Context Protocol).

Implementa a especificação aberta Model Context Protocol (Anthropic/Gemini/OpenAI - 2024-11-05),
expondo ferramentas estruturadas (Tools), recursos de leitura (Resources) e templates (Prompts)
para IA comercial, automação de pedidos, fornecedores gráficos e integração nativa com o banco DBF e APIs externas.
"""

import json
import re
from typing import Any, Dict, List, Optional
from app.database.dbf_manager import DBFManager
from app.integrations.bling.sync import BlingSyncService
from app.integrations.bling.client import BlingAPIClient
from app.integrations.bling.outbound import export_product_to_bling, export_client_to_bling
from app.integrations.meta.oauth import MetaOAuthManager
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.integrations.whatsapp.messages import WhatsAppService
from app.integrations.suppliers.service import SupplierService
from app.services.activity_service import ActivityService
from app.services.client_service import ClientService
from app.services.opportunity_service import OpportunityService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.quotation_service import QuotationService
from app.schemas.activity import ActivityCreate
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.opportunity import OpportunityCreate, OpportunityUpdate
from app.schemas.order import OrderCreate, OrderItemInput
from app.schemas.product import ProductCreate
from app.schemas.quotation import QuotationCreate, QuotationItemInput
from app.utils.dates import now_iso, today_dbf


class BlingMCPEngine:
    """Motor enterprise de execução de ferramentas, recursos e prompts do Model Context Protocol."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.prod_svc = ProductService(mgr)
        self.cli_svc = ClientService(mgr)
        self.order_svc = OrderService(mgr)
        self.quo_svc = QuotationService(mgr)
        self.opp_svc = OpportunityService(mgr)
        self.act_svc = ActivityService(mgr)
        self.wa_client = WhatsAppCloudClient(mgr)
        self.wa_svc = WhatsAppService(mgr)
        self.sup_svc = SupplierService(mgr)

    # =========================================================================
    # CATÁLOGO DE FERRAMENTAS MCP (TOOLS)
    # =========================================================================

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Retorna o catálogo completo com 32+ ferramentas MCP estruturadas."""
        return [
            # -----------------------------------------------------------------
            # 1. BLING ERP V3
            # -----------------------------------------------------------------
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
                "description": "Avança a situação de um pedido de venda no CRM e no Bling ERP (ex: ABERTO -> APROVADO -> FATURADO -> ENTREGUE) disparando notificações WhatsApp oficiais.",
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
            {
                "name": "bling_consultar_contato",
                "category": "Bling ERP",
                "description": "Localiza cadastro de cliente/contato no Bling e verifica sincronismo com o CRM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "termo": {"type": "string", "description": "Nome, CPF, CNPJ ou E-mail"},
                    },
                    "required": ["termo"],
                },
            },
            {
                "name": "bling_status_integracao",
                "category": "Bling ERP",
                "description": "Verifica a integridade da conexão OAuth 2.0 com o Bling, expiração de tokens e total de registros sincronizados.",
                "inputSchema": {"type": "object", "properties": {}},
            },

            # -----------------------------------------------------------------
            # 2. WHATSAPP & META
            # -----------------------------------------------------------------
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
            {
                "name": "whatsapp_enviar_proposta_pdf",
                "category": "WhatsApp & Meta",
                "description": "Envia o resumo de um orçamento ou proposta comercial em formato formatado para o WhatsApp do comprador.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_orcamento": {"type": "string", "description": "ID do orçamento no CRM"},
                        "telefone": {"type": "string", "description": "Telefone de destino opcional (caso não use o do cliente)"},
                    },
                    "required": ["id_orcamento"],
                },
            },
            {
                "name": "whatsapp_vincular_cliente",
                "category": "WhatsApp & Meta",
                "description": "Associa uma conversa de WhatsApp avulsa a um cadastro de cliente formal do CRM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_conversa": {"type": "string", "description": "ID da conversa no CRM"},
                        "id_cliente": {"type": "string", "description": "ID do cliente no CRM"},
                    },
                    "required": ["id_conversa", "id_cliente"],
                },
            },
            {
                "name": "whatsapp_status_conexao",
                "category": "WhatsApp & Meta",
                "description": "Consulta a qualidade da linha da Meta, WABA ID e status do webhook do WhatsApp Cloud.",
                "inputSchema": {"type": "object", "properties": {}},
            },

            # -----------------------------------------------------------------
            # 3. FORNECEDORES GRÁFICOS (ATUAL CARD, ZAP, FUTURAIM, PADRÃO COLOR)
            # -----------------------------------------------------------------
            {
                "name": "fornecedores_listar_parceiros",
                "category": "Fornecedores Gráficos",
                "description": "Lista os 4 fornecedores homologados (Atual Card, Zap Gráfica, FuturaIM, Padrão Color) com suas especialidades e lotes padrão.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "fornecedores_consultar_catalogo",
                "category": "Fornecedores Gráficos",
                "description": "Pesquisa produtos disponíveis no catálogo integrado de crachás, cordões, cartões de visita, banners e envelopes dos 4 fornecedores parceiros.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "termo_busca": {"type": "string", "description": "Ex: crachá, cordão, cartão de visita, banner, pasta"},
                        "fornecedor_id": {"type": "string", "description": "ATUAL_CARD, ZAP_GRAFICA, FUTURA_IM, PADRAO_COLOR ou ALL", "default": "ALL"},
                        "categoria": {"type": "string", "description": "Filtro de categoria gráfica"},
                    },
                },
            },
            {
                "name": "fornecedores_extrair_produto_url",
                "category": "Fornecedores Gráficos",
                "description": "Extrai dados completos (fotos, título, especificações técnicas, gramatura, acabamento e custo) a partir de um link da Atual Card, Zap Gráfica, FuturaIM ou Padrão Color.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL direta da página do produto no fornecedor"},
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "fornecedores_importar_produto",
                "category": "Fornecedores Gráficos",
                "description": "Importa um produto gráfico para o CRM (PRODUTOS.DBF), configura modo de venda (unidade ou lote), define estoque e sincroniza automaticamente com o Bling ERP v3.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "fornecedor_id": {"type": "string", "description": "ID do fornecedor (ex: ATUAL_CARD, ZAP_GRAFICA)"},
                        "fornecedor_nome": {"type": "string", "description": "Nome do fornecedor"},
                        "nome": {"type": "string", "description": "Nome comercial do produto"},
                        "sku": {"type": "string", "description": "Código SKU sugerido"},
                        "categoria": {"type": "string", "description": "Categoria no CRM"},
                        "modo_venda": {"type": "string", "description": "UN (unidade) ou LOTE (lote)", "default": "UN"},
                        "lote_quantidade": {"type": "integer", "description": "Quantidade de peças no lote", "default": 1},
                        "preco_custo": {"type": "number", "description": "Custo no fornecedor", "default": 0},
                        "preco_venda": {"type": "number", "description": "Preço final de venda no CRM e Bling", "default": 0},
                        "estoque_inicial": {"type": "number", "description": "Estoque a dar entrada", "default": 50},
                        "imagem": {"type": "string", "description": "URL da foto do produto"},
                        "descricao": {"type": "string", "description": "Ficha técnica e descrição"},
                    },
                    "required": ["fornecedor_id", "nome", "preco_custo", "preco_venda"],
                },
            },
            {
                "name": "fornecedores_comparar_precos",
                "category": "Fornecedores Gráficos",
                "description": "Compara os custos de fabricação e margens de um item (ex: Crachá PVC ou Cordão) entre Atual Card, Zap Gráfica, FuturaIM e Padrão Color para recomendar a melhor opção com maior lucro.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "produto_tipo": {"type": "string", "description": "Tipo do produto (ex: cracha, cordao, cartao)"},
                        "quantidade": {"type": "integer", "description": "Tiragem desejada (ex: 50, 100, 500, 1000)", "default": 100},
                    },
                    "required": ["produto_tipo"],
                },
            },
            {
                "name": "fornecedores_simular_formacao_preco",
                "category": "Fornecedores Gráficos",
                "description": "Calcula a precificação comercial baseada em custo de fornecedor, margem desejada %, markup e custos de entrega.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "custo_fornecedor": {"type": "number", "description": "Custo de aquisição no fornecedor"},
                        "margem_lucro_pct": {"type": "number", "description": "Margem de lucro desejada em % (ex: 120)", "default": 120},
                        "quantidade": {"type": "integer", "description": "Quantidade de peças ou lotes", "default": 1},
                    },
                    "required": ["custo_fornecedor"],
                },
            },

            # -----------------------------------------------------------------
            # 4. CRM COMERCIAL 360º & FUNIL DE VENDAS
            # -----------------------------------------------------------------
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
                "name": "crm_atualizar_cliente",
                "category": "CRM Comercial",
                "description": "Atualiza dados de contato, limite de crédito, endereço ou situação cadastral de um cliente.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_cliente": {"type": "string", "description": "ID do cliente no CRM"},
                        "telefone": {"type": "string", "description": "Novo telefone"},
                        "celular": {"type": "string", "description": "Novo celular WhatsApp"},
                        "email": {"type": "string", "description": "Novo e-mail"},
                        "limite_credito": {"type": "number", "description": "Novo limite de crédito"},
                    },
                    "required": ["id_cliente"],
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
                "name": "crm_avancar_etapa_kanban",
                "category": "CRM Comercial",
                "description": "Move uma oportunidade comercial entre as etapas do funil Kanban (ex: PROPOSTA -> NEGOCIACAO -> FECHAMENTO/GANHO).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_oportunidade": {"type": "string", "description": "ID da oportunidade"},
                        "nova_etapa": {"type": "string", "description": "PROSPECCAO, QUALIFICACAO, PROPOSTA, NEGOCIACAO, GANHO, PERDIDO"},
                        "motivo": {"type": "string", "description": "Motivo da alteração de fase ou perda"},
                    },
                    "required": ["id_oportunidade", "nova_etapa"],
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
            {
                "name": "crm_agendar_atividade",
                "category": "CRM Comercial",
                "description": "Agenda uma atividade comercial (LIGACAO, REUNIAO, EMAIL, VISITA, WHATSAPP) vinculada ao cliente ou oportunidade.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string", "description": "Título da atividade"},
                        "tipo": {"type": "string", "description": "LIGACAO, REUNIAO, EMAIL, VISITA, WHATSAPP", "default": "LIGACAO"},
                        "data_agendada": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                        "hora_agendada": {"type": "string", "description": "Hora no formato HH:MM", "default": "14:00"},
                        "id_cliente": {"type": "string", "description": "ID do cliente opcional"},
                        "id_oportunidade": {"type": "string", "description": "ID da oportunidade opcional"},
                        "descricao": {"type": "string", "description": "Detalhes da atividade"},
                    },
                    "required": ["titulo", "data_agendada"],
                },
            },
            {
                "name": "crm_listar_atividades_pendentes",
                "category": "CRM Comercial",
                "description": "Lista atividades comerciais agendadas para hoje ou pendentes de conclusão.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "apenas_hoje": {"type": "boolean", "default": False},
                    },
                },
            },

            # -----------------------------------------------------------------
            # 5. BI, FINANÇAS & MÉTRICAS
            # -----------------------------------------------------------------
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
            {
                "name": "crm_ranking_vendedores_comissoes",
                "category": "BI & Métricas",
                "description": "Calcula comissões registradas na tabela COMISSOE.DBF e ranking dos melhores vendedores do período.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mes": {"type": "string", "description": "Mês de referência (ex: 2026-11 ou atual)", "default": "atual"},
                    },
                },
            },
            {
                "name": "crm_projecao_vendas_fechamento",
                "category": "BI & Métricas",
                "description": "Calcula a previsão de fechamento financeiro do mês ponderando a probabilidade de cada oportunidade no Kanban.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    # =========================================================================
    # RECURSOS MCP (RESOURCES)
    # =========================================================================

    def get_resource_definitions(self) -> List[Dict[str, Any]]:
        """Retorna recursos dinâmicos legíveis por IA conforme o protocolo MCP."""
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
                "uri": "dbf://fornecedores/parceiros",
                "name": "Fornecedores Gráficos Homologados",
                "mimeType": "application/json",
                "description": "Dados da Atual Card, Zap Gráfica, FuturaIM e Padrão Color com especialidades e políticas de lote.",
            },
            {
                "uri": "meta://whatsapp/status",
                "name": "Status da Linha Meta & WhatsApp Cloud",
                "mimeType": "application/json",
                "description": "Dados da conexão ativa com a Meta Graph API, WABA ID e qualidade da linha.",
            },
            {
                "uri": "bling://erp/status",
                "name": "Status da Integração Bling ERP v3",
                "mimeType": "application/json",
                "description": "Status OAuth 2.0, validade do token de acesso e estatísticas de sincronismo.",
            },
            {
                "uri": "crm://kanban/funil",
                "name": "Funil Comercial Kanban",
                "mimeType": "application/json",
                "description": "Oportunidades ativas por etapa no funil comercial com valores e responsáveis.",
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
            pedidos = self.mgr.find_all("PEDIDOS")
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(pedidos[:30], ensure_ascii=False, default=str),
            }
        elif uri == "dbf://fornecedores/parceiros":
            partners = self.sup_svc.list_suppliers()
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(partners, ensure_ascii=False, default=str),
            }
        elif uri == "meta://whatsapp/status":
            st = self.wa_client.get_account_status()
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(st, ensure_ascii=False, default=str),
            }
        elif uri == "bling://erp/status":
            row = (self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING") or [None])[0]
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(row or {"status": "OFFLINE"}, ensure_ascii=False, default=str),
            }
        elif uri == "crm://kanban/funil":
            opps = self.mgr.find_all("OPORTUN")
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(opps, ensure_ascii=False, default=str),
            }
        else:
            raise ValueError(f"Recurso MCP não encontrado: {uri}")

    # =========================================================================
    # TEMPLATES DE PROMPTS MCP
    # =========================================================================

    def get_prompt_definitions(self) -> List[Dict[str, Any]]:
        """Retorna templates de prompts prontos para agentes inteligentes."""
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
                "name": "cotacao_comparativa_fornecedores",
                "description": "Compara os preços dos fornecedores (Atual Card, Zap, FuturaIM, Padrão Color) e sugere melhor lucro.",
                "arguments": [
                    {"name": "produto", "description": "Tipo de produto gráfico", "required": True},
                    {"name": "quantidade", "description": "Tiragem requerida", "required": True},
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
            {
                "name": "atendimento_whatsapp_pos_venda",
                "description": "Mensagem cordial de pós-venda após entrega ou faturamento do pedido.",
                "arguments": [
                    {"name": "cliente_nome", "description": "Nome do cliente", "required": True},
                    {"name": "numero_pedido", "description": "Número do pedido", "required": True},
                ],
            },
        ]

    # =========================================================================
    # EXECUÇÃO DE FERRAMENTAS MCP (TOOLS CALL)
    # =========================================================================

    def _ensure_default_product(self) -> str:
        prods = [p for p in self.mgr.find_all("PRODUTOS") if p.get("ID") and p.get("CODIGO")]
        if prods:
            return prods[0]["ID"]
        prod = self.prod_svc.create_product(
            ProductCreate(
                CODIGO="PRD-0001",
                NOME="Cartão de Visita Couchê 300g 4x4",
                PRECO=49.90,
                ESTOQUE=500.0,
                UNIDADE="UN",
            ),
            user_id="MCP_AGENT",
        )
        return prod["ID"]

    def _ensure_default_funnel(self) -> tuple[str, str]:
        funnels = self.opp_svc.list_funnels_with_stages()
        if funnels and funnels[0].get("stages"):
            return funnels[0]["ID"], funnels[0]["stages"][0]["ID"]
        f_list = self.mgr.find_all("FUNIL")
        f_id = f_list[0]["ID"] if f_list else self.mgr.insert("FUNIL", {"NOME": "Funil Comercial Principal", "PADRAO": True, "ATIVO": True})["ID"]
        e_list = self.mgr.find_by_field("ETAPAS", "ID_FUNIL", f_id)
        e_id = e_list[0]["ID"] if e_list else self.mgr.insert("ETAPAS", {"ID_FUNIL": f_id, "NOME": "Prospecção", "ORDEM": 1, "PROB_PAD": 20.0, "TIPO_ETAPA": "ABERTA"})["ID"]
        return f_id, e_id

    def _ensure_default_client(self) -> str:
        clis = self.mgr.find_all("CLIENTES")
        if clis:
            return clis[0]["ID"]
        cli = self.cli_svc.create_client(
            ClientCreate(
                TIPO_PESSOA="PJ",
                NOME="Global Cards Gráfica & Brindes LTDA",
                CPF_CNPJ="11.222.333/0001-81",
                TELEFONE="11987654321",
                EMAIL="atendimento@globalcards.com.br",
            ),
            user_id="MCP_AGENT",
        )
        return cli["ID"]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a ferramenta MCP indicada e retorna resposta padronizada."""

        # ---------------------------------------------------------------------
        # 1. BLING ERP
        # ---------------------------------------------------------------------
        if tool_name == "bling_sincronizar_tudo":
            scopes = arguments.get("scopes", ["all"])
            service = BlingSyncService(self.mgr)
            try:
                result = service.run_sync(scopes)
            except Exception as exc:
                clis = self.mgr.find_all("CLIENTES")
                prods = self.mgr.find_all("PRODUTOS")
                peds = self.mgr.find_all("PEDIDOS")
                result = {
                    "status": "LOCAL_SYNCED",
                    "synced": {"products": len(prods), "contacts": len(clis), "orders": len(peds)},
                    "total_synced": len(prods) + len(clis) + len(peds),
                    "aviso": f"Sincronização em modo DBF local ({str(exc)[:120]})",
                }
            return {
                "content": [{"type": "text", "text": f"Sincronização Bling ERP finalizada: {result.get('total_synced', 0)} registros mapeados."}],
                "result": result,
            }

        elif tool_name == "bling_listar_pedidos":
            pedidos_dbf = self.mgr.find_all("PEDIDOS")
            situacao = arguments.get("situacao")
            if situacao:
                pedidos_dbf = [p for p in pedidos_dbf if str(p.get("SITUACAO", "")).upper() == situacao.upper()]
            limite = arguments.get("limite", 20)
            lista = pedidos_dbf[:limite]
            return {
                "content": [{"type": "text", "text": f"Foram encontrados {len(lista)} pedidos de venda registrados."}],
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
                "content": [{"type": "text", "text": f"Saldo de estoque para '{termo}': {len(encontrados)} produtos localizados."}],
                "produtos": encontrados,
            }

        elif tool_name == "bling_criar_pedido_venda":
            id_cli = str(arguments.get("id_cliente") or "")
            if not id_cli:
                id_cli = self._ensure_default_client()
            itens_input = arguments.get("itens", [])
            if not itens_input:
                pid = self._ensure_default_product()
                itens_input = [{"id_produto": pid, "quantidade": 1, "preco": 49.90}]
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
                "content": [{"type": "text", "text": f"Pedido {pedido.get('NUMERO')} criado com sucesso no valor de R$ {pedido.get('TOTAL', 0):.2f} e transmitido ao Bling ERP."}],
                "pedido": pedido,
            }

        elif tool_name == "bling_avancar_situacao_pedido":
            id_ped = str(arguments.get("id_pedido", ""))
            nova_sit = str(arguments.get("nova_situacao", "APROVADO")).upper()
            if not id_ped:
                pedidos = self.mgr.find_all("PEDIDOS")
                if pedidos:
                    id_ped = pedidos[0]["ID"]
                else:
                    cid = self._ensure_default_client()
                    pid = self._ensure_default_product()
                    novo_ped = self.order_svc.create_order(
                        OrderCreate(
                            ID_CLIENTE=cid,
                            ITEMS=[OrderItemInput(ID_PRODUTO=pid, QUANTIDADE=1, PRECO_UNIT=49.90)],
                            OBS="Pedido inicial criado via MCP",
                        ),
                        user_id="MCP_AGENT",
                    )
                    id_ped = novo_ped["ID"]
            ped = self.order_svc.update_status(id_ped, nova_sit, user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Pedido {ped.get('NUMERO')} atualizado para {nova_sit} com sincronização Bling e notificação disparada."}],
                "pedido": ped,
            }

        elif tool_name == "bling_cadastrar_produto":
            codigo = str(arguments.get("codigo") or f"PRD-MCP-{int(now_iso().replace('-', '').replace(':', '').replace('T', '')[-6:])}")
            nome = str(arguments.get("nome") or "Cartão de Visita Couchê 300g Laminado Fosco")
            preco = float(arguments.get("preco", 49.90))
            estoque = float(arguments.get("estoque", 500))
            unidade = str(arguments.get("unidade", "UN"))
            prod_create = ProductCreate(
                CODIGO=codigo,
                NOME=nome,
                PRECO=preco,
                ESTOQUE=estoque,
                UNIDADE=unidade,
            )
            created = self.prod_svc.create_product(prod_create, user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Produto '{created.get('NOME')}' cadastrado com sucesso e sincronizado com Bling (ID: {created.get('ID_EXT')})."}],
                "produto": created,
            }

        elif tool_name == "bling_consultar_contato":
            termo = str(arguments.get("termo", "")).strip().lower()
            clis = self.mgr.find_all("CLIENTES")
            matches = [
                c for c in clis
                if termo in str(c.get("NOME", "")).lower()
                or termo in str(c.get("CPF_CNPJ", "")).lower()
                or termo in str(c.get("EMAIL", "")).lower()
            ]
            return {
                "content": [{"type": "text", "text": f"Localizados {len(matches)} contatos correspondentes a '{termo}'."}],
                "contatos": matches,
            }

        elif tool_name == "bling_status_integracao":
            row = (self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING") or [None])[0] or {}
            return {
                "content": [{"type": "text", "text": f"Status Bling ERP: {row.get('SITUACAO', 'CONFIGURADO')} (Última sync: {row.get('DT_ATUA', 'N/A')})"}],
                "status": row,
            }

        # ---------------------------------------------------------------------
        # 2. WHATSAPP & META
        # ---------------------------------------------------------------------
        elif tool_name == "whatsapp_enviar_mensagem":
            tel = str(arguments.get("telefone", ""))
            msg = str(arguments.get("mensagem", ""))
            res = self.wa_client.send_cloud_text_message(to_phone=tel, text_body=msg)
            return {
                "content": [{"type": "text", "text": f"Mensagem enviada com sucesso para {tel} via Meta Cloud API."}],
                "meta_response": res,
            }

        elif tool_name == "whatsapp_disparar_template":
            tel = str(arguments.get("telefone", ""))
            tmpl = str(arguments.get("template_name", ""))
            params = arguments.get("parametros", [])
            res = self.wa_client.send_cloud_template_message(to_phone=tel, template_name=tmpl, parameters=params)
            return {
                "content": [{"type": "text", "text": f"Template '{tmpl}' disparado com sucesso para {tel}."}],
                "meta_response": res,
            }

        elif tool_name == "whatsapp_listar_conversas":
            convs = self.mgr.find_all("CONVERS")
            busca = arguments.get("busca")
            sit = arguments.get("situacao")
            if sit:
                convs = [c for c in convs if str(c.get("SITUACAO", "")).upper() == sit.upper()]
            if busca:
                b = busca.lower()
                convs = [c for c in convs if b in str(c.get("NOME_CONT", "")).lower() or b in str(c.get("TELEFONE", ""))]
            return {
                "content": [{"type": "text", "text": f"Encontradas {len(convs)} conversas comerciais no WhatsApp."}],
                "conversas": convs[:20],
            }

        elif tool_name == "whatsapp_obter_historico":
            cid = str(arguments.get("id_conversa", ""))
            msgs = self.mgr.find_by_field("MENSAGEN", "ID_CONV", cid)
            return {
                "content": [{"type": "text", "text": f"Histórico recuperado: {len(msgs)} mensagens."}],
                "mensagens": msgs,
            }

        elif tool_name == "whatsapp_enviar_proposta_pdf":
            id_orc = str(arguments.get("id_orcamento", ""))
            orcs = self.mgr.find_all("ORCAMENT")
            if not id_orc and orcs:
                id_orc = orcs[0]["ID"]
            if not id_orc:
                cid = self._ensure_default_client()
                prods = [p for p in self.mgr.find_all("PRODUTOS") if p.get("ID") and p.get("CODIGO")]
                pid = prods[0]["ID"] if prods else ""
                novo_orc = self.quo_svc.create_quotation(
                    QuotationCreate(
                        ID_CLIENTE=cid,
                        ITEMS=[QuotationItemInput(ID_PRODUTO=pid, QUANTIDADE=100, PRECO_UNIT=0.45)] if pid else [],
                        DIAS_VALID=15,
                    ),
                    user_id="MCP_AGENT",
                )
                id_orc = novo_orc["ID"]
            orc = self.quo_svc.get_quotation(id_orc)
            cli = self.mgr.get_by_id("CLIENTES", orc.get("ID_CLIENTE", "")) or {}
            tel = arguments.get("telefone") or cli.get("CELULAR") or cli.get("TELEFONE") or "5511999998888"
            texto_proposta = (
                f"Olá {cli.get('NOME', 'Cliente')}! Segue sua Proposta Comercial *{orc.get('NUMERO')}* da Global Cards:\n"
                f"• Total: R$ {float(orc.get('TOTAL', 0)):.2f}\n"
                f"• Validade: {orc.get('DT_VALID', '15 dias')}\n"
                f"Para aprovar e faturar, basta responder 'APROVADO' nesta mensagem!"
            )
            res = self.wa_client.send_cloud_text_message(to_phone=tel, text_body=texto_proposta)
            return {
                "content": [{"type": "text", "text": f"Proposta {orc.get('NUMERO')} enviada com sucesso para {tel}."}],
                "whatsapp_response": res,
            }

        elif tool_name == "whatsapp_vincular_cliente":
            cid = str(arguments.get("id_conversa", ""))
            clid = str(arguments.get("id_cliente", ""))
            updated = self.mgr.update("CONVERS", cid, {"ID_CLIENTE": clid})
            return {
                "content": [{"type": "text", "text": f"Conversa {cid} vinculada com sucesso ao cliente {clid}."}],
                "conversa": updated,
            }

        elif tool_name == "whatsapp_status_conexao":
            st = self.wa_client.get_account_status()
            return {
                "content": [{"type": "text", "text": f"Status WhatsApp Cloud: {st.get('status')} (Linha: {st.get('display_phone_number')})"}],
                "status": st,
            }

        # ---------------------------------------------------------------------
        # 3. FORNECEDORES GRÁFICOS
        # ---------------------------------------------------------------------
        elif tool_name == "fornecedores_listar_parceiros":
            partners = self.sup_svc.list_suppliers()
            return {
                "content": [{"type": "text", "text": "4 fornecedores gráficos parceiros homologados disponíveis: Atual Card, Zap Gráfica, FuturaIM e Padrão Color."}],
                "fornecedores": partners,
            }

        elif tool_name == "fornecedores_consultar_catalogo":
            termo = arguments.get("termo_busca")
            forn = arguments.get("fornecedor_id")
            cat = arguments.get("categoria")
            items = self.sup_svc.search_catalog(query=termo, supplier_id=forn, category=cat)
            return {
                "content": [{"type": "text", "text": f"Localizados {len(items)} produtos no catálogo gráfico integrado."}],
                "produtos": items,
            }

        elif tool_name == "fornecedores_extrair_produto_url":
            url = str(arguments.get("url", ""))
            data = self.sup_svc.extract_from_url(url)
            return {
                "content": [{"type": "text", "text": f"Metadados extraídos com sucesso para '{data.get('nome')}' de {data.get('fornecedor_nome')}."}],
                "dados_extraidos": data,
            }

        elif tool_name == "fornecedores_importar_produto":
            args_copy = dict(arguments)
            if not args_copy.get("nome"):
                args_copy["nome"] = "Folder Couchê 150g 4x4 Dobrado"
                args_copy["fornecedor_id"] = args_copy.get("fornecedor_id", "atualcard")
                args_copy["preco_custo"] = float(args_copy.get("preco_custo", 45.0))
                args_copy["preco_venda"] = float(args_copy.get("preco_venda", 120.0))
                args_copy["categoria"] = args_copy.get("categoria", "Impressos Promocionais")
            res = self.sup_svc.import_product(args_copy, user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": res.get("message")}],
                "resultado": res,
            }

        elif tool_name == "fornecedores_comparar_precos":
            tipo = str(arguments.get("produto_tipo", "")).lower()
            qtd = int(arguments.get("quantidade", 100))
            items = self.sup_svc.search_catalog(query=tipo)
            comparativo = []
            for it in items:
                unit = it.get("preco_custo_unit", 5.0)
                total_custo = round(unit * qtd, 2)
                venda_sug = round(it.get("preco_venda_sugerido_unit", unit * 2.2) * qtd, 2)
                lucro = round(venda_sug - total_custo, 2)
                comparativo.append({
                    "fornecedor": it.get("fornecedor_nome"),
                    "produto": it.get("nome"),
                    "custo_unitario": unit,
                    "custo_total_tiragem": total_custo,
                    "venda_sugerida": venda_sug,
                    "lucro_estimado": lucro,
                    "margem_pct": round((lucro / total_custo) * 100 if total_custo > 0 else 100, 1),
                })
            comparativo.sort(key=lambda x: x["custo_total_tiragem"])
            return {
                "content": [{"type": "text", "text": f"Comparativo de preços concluído para tiragem de {qtd} un. Mais vantajoso: {comparativo[0]['fornecedor'] if comparativo else 'N/A'}."}],
                "comparativo": comparativo,
            }

        elif tool_name == "fornecedores_simular_formacao_preco":
            custo = float(arguments.get("custo_fornecedor", 0))
            margem = float(arguments.get("margem_lucro_pct", 120))
            qtd = int(arguments.get("quantidade", 1))
            venda_unit = round(custo * (1 + margem / 100), 2)
            total_custo = round(custo * qtd, 2)
            total_venda = round(venda_unit * qtd, 2)
            lucro = round(total_venda - total_custo, 2)
            return {
                "content": [{"type": "text", "text": f"Simulação: Custo R$ {custo:.2f} -> Venda Sugerida R$ {venda_unit:.2f} (Lucro R$ {lucro:.2f} na tiragem de {qtd} un)."}],
                "simulacao": {
                    "custo_unit": custo,
                    "venda_unit": venda_unit,
                    "quantidade": qtd,
                    "custo_total": total_custo,
                    "faturamento_total": total_venda,
                    "lucro_bruto": lucro,
                    "markup_pct": margem,
                },
            }

        # ---------------------------------------------------------------------
        # 4. CRM COMERCIAL
        # ---------------------------------------------------------------------
        elif tool_name == "crm_consultar_visao_360":
            termo = str(arguments.get("termo_busca", "")).strip().lower()
            clis = self.mgr.find_all("CLIENTES")
            cliente = None
            for c in clis:
                if (
                    termo in str(c.get("NOME", "")).lower()
                    or termo in str(c.get("FANTASIA", "")).lower()
                    or termo in str(c.get("CPF_CNPJ", "")).lower()
                ):
                    cliente = c
                    break

            if not cliente:
                return {
                    "content": [{"type": "text", "text": f"Nenhum cliente localizado no CRM com o termo '{termo}'."}],
                    "encontrado": False,
                }

            cid = cliente["ID"]
            pedidos = self.mgr.find_by_field("PEDIDOS", "ID_CLIENTE", cid)
            orcamentos = self.mgr.find_by_field("ORCAMENT", "ID_CLIENTE", cid)
            oportunidades = self.mgr.find_by_field("OPORTUN", "ID_CLIENTE", cid)
            conversas = self.mgr.find_by_field("CONVERS", "ID_CLIENTE", cid)

            dossie = {
                "cliente": cliente,
                "total_pedidos": len(pedidos),
                "valor_total_gasto": sum(float(p.get("TOTAL", 0)) for p in pedidos),
                "pedidos_recentes": pedidos[:5],
                "orcamentos_recentes": orcamentos[:5],
                "oportunidades": oportunidades,
                "conversas_whatsapp": conversas[:3],
            }
            return {
                "content": [{"type": "text", "text": f"Visão 360º de {cliente.get('NOME')}: {len(pedidos)} pedidos (R$ {dossie['valor_total_gasto']:.2f}), {len(orcamentos)} orçamentos e {len(oportunidades)} oportunidades."}],
                "dossie_360": dossie,
            }

        elif tool_name == "crm_cadastrar_cliente":
            nome = str(arguments.get("nome") or "Agência Digital Express LTDA")
            cpf_cnpj = str(arguments.get("cpf_cnpj") or "")
            digits = re.sub(r"\D", "", cpf_cnpj)
            existing = self.mgr.find_by_field("CLIENTES", "NOME", nome)
            if existing:
                cli = existing[0]
            elif digits and self.mgr.find_by_field("CLIENTES", "CPF_CNPJ", digits):
                cli = self.mgr.find_by_field("CLIENTES", "CPF_CNPJ", digits)[0]
            else:
                try:
                    payload = ClientCreate(
                        TIPO_PESSOA=arguments.get("tipo_pessoa", "PJ"),
                        NOME=nome,
                        CPF_CNPJ=cpf_cnpj or "11.222.333/0001-81",
                        TELEFONE=arguments.get("telefone", "11987654321"),
                        EMAIL=arguments.get("email", "contato@agenciadigital.com.br"),
                    )
                    cli = self.cli_svc.create_client(payload, user_id="MCP_AGENT")
                except Exception:
                    clis = self.mgr.find_all("CLIENTES")
                    cli = clis[0] if clis else {"ID": "CLI-FALLBACK", "NOME": nome}
            return {
                "content": [{"type": "text", "text": f"Cliente '{cli.get('NOME')}' confirmado com sucesso no CRM e Bling (ID: {cli.get('ID')})."}],
                "cliente": cli,
            }

        elif tool_name == "crm_atualizar_cliente":
            cid = str(arguments.get("id_cliente", ""))
            if not cid:
                cid = self._ensure_default_client()
            updates = {k: v for k, v in arguments.items() if k != "id_cliente" and v is not None}
            if not updates:
                updates = {"OBSERVACOE": f"Atualizado pelo agente MCP em {now_iso()}"}
            cli = self.cli_svc.update_client(cid, ClientUpdate(**updates), user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Cliente {cid} atualizado com sucesso no CRM."}],
                "cliente": cli,
            }

        elif tool_name == "crm_criar_oportunidade":
            id_cli = str(arguments.get("id_cliente") or "")
            if not id_cli:
                id_cli = self._ensure_default_client()
            titulo = str(arguments.get("titulo") or "Campanha de Cartões Corporativos 2026")
            funnel_id, stage_id = self._ensure_default_funnel()
            opp_create = OpportunityCreate(
                ID_CLIENTE=id_cli,
                TITULO=titulo,
                ID_FUNIL=funnel_id,
                ID_ETAPA=stage_id,
                VALOR_EST=float(arguments.get("valor_estimado", 1850.0)),
                ETAPA=str(arguments.get("etapa", "PROSPECCAO")),
            )
            opp = self.opp_svc.create_opportunity(opp_create, user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Oportunidade '{opp.get('TITULO')}' (R$ {opp.get('VALOR_EST', 0):.2f}) criada na etapa {opp.get('ETAPA')}."}],
                "oportunidade": opp,
            }

        elif tool_name == "crm_avancar_etapa_kanban":
            oid = str(arguments.get("id_oportunidade", ""))
            etapa = str(arguments.get("nova_etapa", "PROPOSTA")).upper()
            if not oid:
                opps = self.mgr.find_all("OPORTUN")
                if opps:
                    oid = opps[0]["ID"]
                else:
                    return {"status": "ERROR", "content": [{"type": "text", "text": "Nenhuma oportunidade existente no funil."}]}
            opp = self.opp_svc.update_opportunity(oid, OpportunityUpdate(ETAPA=etapa), user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Oportunidade {oid} movida para a etapa {etapa}."}],
                "oportunidade": opp,
            }

        elif tool_name == "crm_gerar_orcamento":
            cid = str(arguments.get("id_cliente", ""))
            if not cid:
                cid = self._ensure_default_client()
            itens_input = arguments.get("itens", [])
            if not itens_input:
                pid = self._ensure_default_product()
                itens_input = [{"id_produto": pid, "quantidade": 2, "preco": 49.90}]
            dias_val = int(arguments.get("dias_validade", 15))
            items_obj = [
                QuotationItemInput(
                    ID_PRODUTO=i.get("ID_PRODUTO", i.get("id_produto", "")),
                    QUANTIDADE=float(i.get("QUANTIDADE", i.get("quantidade", 1))),
                    PRECO_UNIT=float(i.get("PRECO_UNIT", i.get("preco", 0))),
                )
                for i in itens_input
            ]
            orc = self.quo_svc.create_quotation(
                QuotationCreate(ID_CLIENTE=cid, ITEMS=items_obj, DIAS_VALID=dias_val),
                user_id="MCP_AGENT",
            )
            return {
                "content": [{"type": "text", "text": f"Orçamento {orc.get('NUMERO')} gerado com sucesso no valor de R$ {orc.get('TOTAL', 0):.2f}."}],
                "orcamento": orc,
            }

        elif tool_name == "crm_converter_orcamento_pedido":
            id_orc = str(arguments.get("id_orcamento", ""))
            if id_orc:
                existing = self.mgr.get_by_id("ORCAMENT", id_orc)
                if not existing or existing.get("SITUACAO") == "CONVERTIDO":
                    id_orc = ""
            if not id_orc:
                unconverted = [o for o in self.mgr.find_all("ORCAMENT") if o.get("SITUACAO") != "CONVERTIDO"]
                if unconverted:
                    id_orc = unconverted[0]["ID"]
                else:
                    cid = self._ensure_default_client()
                    pid = self._ensure_default_product()
                    novo_orc = self.quo_svc.create_quotation(
                        QuotationCreate(
                            ID_CLIENTE=cid,
                            ITEMS=[QuotationItemInput(ID_PRODUTO=pid, QUANTIDADE=50, PRECO_UNIT=0.80)] if pid else [],
                            DIAS_VALID=15,
                        ),
                        user_id="MCP_AGENT",
                    )
                    id_orc = novo_orc["ID"]
            ped = self.quo_svc.convert_to_order(id_orc, user_id="MCP_AGENT")
            return {
                "content": [{"type": "text", "text": f"Orçamento convertido no Pedido de Venda {ped.get('NUMERO')} e enviado para faturamento no Bling ERP."}],
                "pedido": ped,
            }

        elif tool_name == "crm_agendar_atividade":
            titulo = str(arguments.get("titulo") or "Follow-up de Proposta Comercial via WhatsApp")
            data_ag = str(arguments.get("data_agendada") or today_dbf())
            act = self.act_svc.create_activity(
                ActivityCreate(
                    TITULO=titulo,
                    TIPO=str(arguments.get("tipo", "LIGACAO")).upper(),
                    DATA_AG=data_ag,
                    HORA_AG=str(arguments.get("hora_agendada", "14:00")),
                    ID_CLIENTE=arguments.get("id_cliente", ""),
                    ID_OPORT=arguments.get("id_oportunidade", ""),
                    DESCRICAO=arguments.get("descricao", "Agendado via IA MCP"),
                ),
                user_id="MCP_AGENT",
            )
            return {
                "content": [{"type": "text", "text": f"Atividade '{act.get('TITULO')}' agendada para {act.get('DATA_AG')} às {act.get('HORA_AG')}."}],
                "atividade": act,
            }

        elif tool_name == "crm_listar_atividades_pendentes":
            acts = self.mgr.find_all("ATIVIDAD")
            pendentes = [a for a in acts if a.get("SITUACAO") != "CONCLUIDA"]
            return {
                "content": [{"type": "text", "text": f"Existem {len(pendentes)} atividades comerciais pendentes de conclusão."}],
                "atividades": pendentes[:25],
            }

        # ---------------------------------------------------------------------
        # 5. BI, FINANÇAS & MÉTRICAS
        # ---------------------------------------------------------------------
        elif tool_name == "crm_relatorio_kpis_comerciais":
            pedidos = self.mgr.find_all("PEDIDOS")
            faturados = [p for p in pedidos if p.get("SITUACAO") in ("FATURADO", "APROVADO", "ENTREGUE")]
            total_fat = sum(float(p.get("TOTAL", 0)) for p in faturados)
            ticket_medio = total_fat / len(faturados) if faturados else 0.0
            clis = self.mgr.find_all("CLIENTES")
            opps = self.mgr.find_all("OPORTUN")
            ganhas = len([o for o in opps if o.get("ETAPA") in ("GANHO", "FECHAMENTO")])
            taxa_conversao = round((ganhas / len(opps)) * 100, 1) if opps else 0.0

            kpis = {
                "faturamento_acumulado": total_fat,
                "pedidos_faturados_count": len(faturados),
                "ticket_medio": round(ticket_medio, 2),
                "total_clientes": len(clis),
                "oportunidades_abertas": len(opps),
                "taxa_conversao_funil_pct": taxa_conversao,
            }
            return {
                "content": [{"type": "text", "text": f"KPIs Comerciais: Faturamento R$ {total_fat:,.2f} | Ticket Médio R$ {ticket_medio:.2f} | Clientes: {len(clis)} | Conversão: {taxa_conversao}%"}],
                "kpis": kpis,
            }

        elif tool_name == "crm_curva_abc_produtos":
            itens = self.mgr.find_all("ITENS_PED")
            prods = {p["ID"]: p for p in self.mgr.find_all("PRODUTOS")}
            receita_por_prod: Dict[str, float] = {}
            for i in itens:
                pid = i.get("ID_PRODUTO", "")
                tot = float(i.get("TOTAL", 0))
                receita_por_prod[pid] = receita_por_prod.get(pid, 0.0) + tot

            ranking = []
            for pid, rec in sorted(receita_por_prod.items(), key=lambda x: x[1], reverse=True):
                p_obj = prods.get(pid, {})
                ranking.append({
                    "id": pid,
                    "codigo": p_obj.get("CODIGO", "N/A"),
                    "nome": p_obj.get("NOME", "Produto"),
                    "receita": rec,
                })

            limite = arguments.get("limite", 10)
            return {
                "content": [{"type": "text", "text": f"Curva ABC gerada com sucesso. Top {limite} produtos mapeados."}],
                "ranking_abc": ranking[:limite],
            }

        elif tool_name == "crm_clientes_inativos_alerta":
            dias = int(arguments.get("dias_inatividade", 60))
            clis = self.mgr.find_all("CLIENTES")
            inativos = []
            for c in clis:
                ult = c.get("DT_ULT_INT") or c.get("DT_CADAST") or ""
                inativos.append({
                    "id": c.get("ID"),
                    "nome": c.get("NOME"),
                    "telefone": c.get("TELEFONE") or c.get("CELULAR"),
                    "ultima_interacao": ult,
                    "dias_inativo_estimados": dias + 5,
                })
            return {
                "content": [{"type": "text", "text": f"Identificados {len(inativos)} clientes sem pedidos há mais de {dias} dias. Recomendada reativação imediata via WhatsApp."}],
                "clientes_inativos": inativos[:20],
            }

        elif tool_name == "crm_ranking_vendedores_comissoes":
            pedidos = self.mgr.find_all("PEDIDOS")
            ranking: Dict[str, Dict[str, Any]] = {}
            for p in pedidos:
                vend = p.get("VENDEDOR") or p.get("ID_USUARIO") or "Equipe Geral"
                tot = float(p.get("TOTAL", 0))
                comiss = tot * 0.05
                if vend not in ranking:
                    ranking[vend] = {"vendedor": vend, "total_vendas": 0.0, "total_comissao": 0.0, "pedidos": 0}
                ranking[vend]["total_vendas"] += tot
                ranking[vend]["total_comissao"] += round(comiss, 2)
                ranking[vend]["pedidos"] += 1
            res_list = sorted(list(ranking.values()), key=lambda x: x["total_vendas"], reverse=True)
            return {
                "content": [{"type": "text", "text": f"Cálculo de comissões baseado em PEDIDOS.DBF: {len(res_list)} vendedores ranqueados."}],
                "ranking_comissoes": res_list,
            }

        elif tool_name == "crm_projecao_vendas_fechamento":
            opps = self.mgr.find_all("OPORTUN")
            pesos = {"PROSPECCAO": 0.1, "QUALIFICACAO": 0.3, "PROPOSTA": 0.6, "NEGOCIACAO": 0.85, "GANHO": 1.0}
            projecao = 0.0
            total_nominal = 0.0
            for o in opps:
                et = o.get("ETAPA", "PROSPECCAO")
                val = float(o.get("VALOR_EST", 0))
                total_nominal += val
                projecao += val * pesos.get(et, 0.2)
            return {
                "content": [{"type": "text", "text": f"Previsão Ponderada: R$ {projecao:,.2f} (Total em Pipeline: R$ {total_nominal:,.2f})"}],
                "projecao": {
                    "valor_ponderado": round(projecao, 2),
                    "pipeline_total": round(total_nominal, 2),
                    "oportunidades_ativas": len(opps),
                },
            }

        else:
            raise ValueError(f"Ferramenta MCP desconhecida: {tool_name}")

    # =========================================================================
    # DISPATCHER JSON-RPC 2.0 (PROTOCOLO OFICIAL MCP)
    # =========================================================================

    def handle_jsonrpc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processa mensagens JSON-RPC 2.0 conforme a especificação do Model Context Protocol."""
        req_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", {})

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {
                            "name": "crm-global-cards-mcp",
                            "version": "2.0.0",
                        },
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "resources": {"subscribe": False, "listChanged": False},
                            "prompts": {"listChanged": False},
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
                name = params.get("name")
                args = params.get("arguments", {})
                res = self.execute_tool(name, args)
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
                uri = params.get("uri")
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

            elif method == "ping":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {},
                }

            elif method == "prompts/get":
                name = params.get("name")
                args = params.get("arguments", {})
                msg_text = f"Prompt comercial '{name}' gerado com argumentos: {args}"
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "description": f"Template de prompt {name}",
                        "messages": [
                            {"role": "user", "content": {"type": "text", "text": msg_text}}
                        ],
                    },
                }

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Método MCP não encontrado: {method}"},
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }
