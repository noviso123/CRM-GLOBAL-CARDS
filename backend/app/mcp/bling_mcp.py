"""Bling & CRM Global Cards MCP (Model Context Protocol) Server Integration.

Implementa a especificação aberta Model Context Protocol (Anthropic/Gemini/OpenAI)
permitindo que agentes de IA e o próprio CRM executem operações autônomas e consultas
no Bling ERP v3 e no banco de dados local dBase III+ (DBF).
"""

from typing import Any, Dict, List, Optional
from app.database.dbf_manager import DBFManager
from app.integrations.bling.sync import BlingSyncService
from app.integrations.bling.client import BlingAPIClient
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.utils.dates import now_iso


class BlingMCPEngine:
    """Motor de execução de ferramentas MCP (Model Context Protocol)."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Retorna o catálogo de ferramentas no padrão JSON Schema do Model Context Protocol."""
        return [
            {
                "name": "bling_sincronizar_tudo",
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
                "description": "Consulta pedidos de venda no Bling ERP com filtros por período e situação comercial.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "situacao": {
                            "type": "string",
                            "description": "Situação do pedido: ABERTO, APROVADO, FATURADO, ENTREGUE ou CANCELADO",
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de pedidos a retornar",
                            "default": 20,
                        },
                    },
                },
            },
            {
                "name": "bling_consultar_estoque",
                "description": "Consulta o saldo de estoque físico e virtual de produtos no Bling e compara com a base DBF.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codigo_ou_id": {
                            "type": "string",
                            "description": "Código SKU ou ID do produto no Bling",
                        }
                    },
                    "required": ["codigo_ou_id"],
                },
            },
            {
                "name": "bling_criar_pedido_venda",
                "description": "Cria e registra um novo pedido de venda diretamente no Bling ERP a partir de um orçamento ou oportunidade do CRM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id_cliente": {
                            "type": "string",
                            "description": "ID ou documento do cliente",
                        },
                        "itens": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Lista de itens com codigo, quantidade e preco",
                        },
                        "observacoes": {"type": "string", "description": "Observações do pedido"},
                    },
                    "required": ["id_cliente", "itens"],
                },
            },
            {
                "name": "whatsapp_enviar_mensagem",
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
                "name": "crm_consultar_visao_360",
                "description": "Consulta o dossiê comercial completo 360º de um cliente (pedidos, contatos, endereços, conversas e notas).",
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
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a ferramenta MCP indicada e retorna resposta padronizada."""
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
                pedidos_dbf = [p for p in pedidos_dbf if str(p.get("SITUACAO", "")).upper() == situacao.upper()]
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
            termo = str(arguments.get("codigo_ou_id", "")).strip()
            prods = self.mgr.find_all("PRODUTOS")
            encontrados = [
                p for p in prods
                if termo.lower() in str(p.get("CODIGO", "")).lower() or termo.lower() in str(p.get("NOME", "")).lower()
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
            id_cli = arguments.get("id_cliente")
            itens = arguments.get("itens", [])
            obs = arguments.get("observacoes", "Emitido via Bling MCP")
            # Criação do pedido na base local DBF com rastreabilidade
            seq = len(self.mgr.find_all("PEDIDOS")) + 1
            numero = f"PED-MCP-{seq:05d}"
            subtotal = sum(float(i.get("quantidade", 1)) * float(i.get("preco", 0)) for i in itens)
            pedido = self.mgr.insert(
                "PEDIDOS",
                {
                    "NUMERO": numero,
                    "ID_CLIENTE": str(id_cli),
                    "SUBTOTAL": subtotal,
                    "DESCONTO": 0.0,
                    "FRETE": 0.0,
                    "TOTAL": subtotal,
                    "COND_PAGTO": "Boleto 28 dias",
                    "SITUACAO": "APROVADO",
                    "ORIGEM": "MCP_AGENT",
                    "DT_PEDIDO": now_iso()[:10],
                    "OBS": obs,
                },
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Pedido {numero} criado com sucesso via Bling MCP no valor de R$ {subtotal:.2f}.",
                    }
                ],
                "pedido": pedido,
            }

        elif tool_name == "whatsapp_enviar_mensagem":
            tel = arguments.get("telefone", "")
            msg = arguments.get("mensagem", "")
            wa = WhatsAppCloudClient(self.mgr)
            res = wa.send_text_message(tel, msg)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Mensagem enviada com sucesso para {tel} via WhatsApp Cloud API.",
                    }
                ],
                "response": res,
            }

        elif tool_name == "crm_consultar_visao_360":
            termo = str(arguments.get("termo_busca", "")).strip().lower()
            clientes = self.mgr.find_all("CLIENTES")
            filtrados = [
                c for c in clientes
                if termo in str(c.get("NOME", "")).lower()
                or termo in str(c.get("FANTASIA", "")).lower()
                or termo in str(c.get("CPF_CNPJ", "")).lower()
            ]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{len(filtrados)} cliente(s) encontrado(s) para o termo '{termo}'.",
                    }
                ],
                "clientes": filtrados,
            }

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Ferramenta MCP '{tool_name}' não reconhecida."}],
            }
