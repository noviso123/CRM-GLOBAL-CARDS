from typing import Any, Dict, List
from app.database.dbf_manager import DBFManager
from app.integrations.bling.client import BlingAPIClient
from app.integrations.bling.contacts import fetch_bling_contacts
from app.integrations.bling.orders import fetch_bling_orders
from app.integrations.bling.products import fetch_bling_products
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso, today_dbf
from app.utils.validators import normalize_digits


class BlingSyncService:
    """Sincroniza Produtos, Clientes/Contatos e Pedidos com o Bling respeitando a matriz de propriedade de dados."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.api = BlingAPIClient(mgr)
        self.notif = NotificationService(mgr)

    def upsert_bling_product(self, b_prod: Dict[str, Any]) -> Dict[str, Any]:
        ext_id = str(b_prod.get("id", "")).strip()
        codigo = str(b_prod.get("codigo", "") or f"BLG-{ext_id}").strip()
        nome = str(b_prod.get("nome", "Produto Bling")).strip()
        preco = float(b_prod.get("preco", 0.0) or 0.0)
        estoque_info = b_prod.get("estoque") or {}
        estoque = float(
            estoque_info.get("saldoVirtualTotal", b_prod.get("estoqueAtual", 0.0)) or 0.0
        )
        unidade = str(b_prod.get("unidade", "UN") or "UN").strip()
        situacao = "ATIVO" if str(b_prod.get("situacao", "A")).upper() in ("A", "ATIVO") else "INATIVO"

        existing = self.mgr.find_by_field("PRODUTOS", "ID_EXT", ext_id) if ext_id else []
        if not existing and codigo:
            existing = self.mgr.find_by_field("PRODUTOS", "CODIGO", codigo)

        if existing:
            curr = existing[0]
            # Atualiza SOMENTE os campos cuja fonte principal é o Bling (preserva DESC_MAX, DESTAQUE, DOC_REF locais)
            updated = self.mgr.update(
                "PRODUTOS",
                curr["ID"],
                {
                    "CODIGO": codigo,
                    "NOME": nome,
                    "PRECO": preco,
                    "ESTOQUE": estoque,
                    "UNIDADE": unidade,
                    "SITUACAO": situacao,
                    "ID_EXT": ext_id,
                },
            )
            return {"action": "UPDATED", "record": updated or curr}

        created = self.mgr.insert(
            "PRODUTOS",
            {
                "CODIGO": codigo,
                "NOME": nome,
                "DESC_CURTA": str(b_prod.get("descricaoCurta", "") or ""),
                "UNIDADE": unidade,
                "PRECO": preco,
                "ESTOQUE": estoque,
                "DESC_MAX": 10.0,
                "DESTAQUE": False,
                "SITUACAO": situacao,
                "ORIGEM": "BLING",
                "ID_EXT": ext_id,
            },
        )
        return {"action": "CREATED", "record": created}

    def upsert_bling_client(self, b_contact: Dict[str, Any]) -> Dict[str, Any]:
        ext_id = str(b_contact.get("id", "")).strip()
        doc = normalize_digits(b_contact.get("numeroDocumento", ""))
        nome = str(b_contact.get("nome", "Cliente Bling")).strip()
        fantasia = str(b_contact.get("fantasia", "") or "").strip()
        tipo = "PF" if str(b_contact.get("tipo", "J")).upper() == "F" or len(doc) == 11 else "PJ"

        existing = self.mgr.find_by_field("CLIENTES", "ID_EXT", ext_id) if ext_id else []
        if not existing and doc:
            existing = self.mgr.find_by_field("CLIENTES", "CPF_CNPJ", doc)

        endereco_obj = b_contact.get("endereco", {}).get("geral", {}) if isinstance(b_contact.get("endereco"), dict) else {}

        if existing:
            curr = existing[0]
            # Preserva ID_RESP, OBS_CURTA, DOC_REF e histórico do CRM
            updated = self.mgr.update(
                "CLIENTES",
                curr["ID"],
                {
                    "NOME": nome,
                    "FANTASIA": fantasia or curr.get("FANTASIA", ""),
                    "CPF_CNPJ": doc or curr.get("CPF_CNPJ", ""),
                    "EMAIL": str(b_contact.get("email", "") or curr.get("EMAIL", "")),
                    "TELEFONE": str(b_contact.get("telefone", "") or curr.get("TELEFONE", "")),
                    "CELULAR": str(b_contact.get("celular", "") or curr.get("CELULAR", "")),
                    "ID_EXT": ext_id,
                },
            )
            return {"action": "UPDATED", "record": updated or curr}

        created = self.mgr.insert(
            "CLIENTES",
            {
                "CODIGO": self.mgr.next_sequence_code("CLIENTES", "CLI"),
                "TIPO_PES": tipo,
                "NOME": nome,
                "FANTASIA": fantasia,
                "CPF_CNPJ": doc,
                "EMAIL": str(b_contact.get("email", "") or ""),
                "TELEFONE": str(b_contact.get("telefone", "") or ""),
                "CELULAR": str(b_contact.get("celular", "") or ""),
                "ENDERECO": str(endereco_obj.get("endereco", "") or ""),
                "NUMERO": str(endereco_obj.get("numero", "") or ""),
                "BAIRRO": str(endereco_obj.get("bairro", "") or ""),
                "CIDADE": str(endereco_obj.get("municipio", "") or ""),
                "UF": str(endereco_obj.get("uf", "") or ""),
                "CEP": str(endereco_obj.get("cep", "") or ""),
                "PAIS": "Brasil",
                "SITUACAO": "ATIVO",
                "ORIGEM": "BLING",
                "ID_EXT": ext_id,
                "DT_ULT_INT": now_iso(),
            },
        )
        return {"action": "CREATED", "record": created}

    def upsert_bling_order(self, b_order: Dict[str, Any]) -> Dict[str, Any]:
        ext_id = str(b_order.get("id", "")).strip()
        numero = f"BLG-{b_order.get('numero', ext_id)}"
        existing = self.mgr.find_by_field("PEDIDOS", "ID_EXT", ext_id) if ext_id else []
        if not existing:
            existing = self.mgr.find_by_field("PEDIDOS", "NUMERO", numero)

        contato = b_order.get("contato") or {}
        cli_ext_id = str(contato.get("id", "")).strip()
        clients = self.mgr.find_by_field("CLIENTES", "ID_EXT", cli_ext_id) if cli_ext_id else []
        if not clients:
            c_res = self.upsert_bling_client(
                {"id": cli_ext_id or f"C-{ext_id}", "nome": contato.get("nome", "Cliente Bling"), "numeroDocumento": contato.get("numeroDocumento", "")}
            )
            client_id = c_res["record"]["ID"]
        else:
            client_id = clients[0]["ID"]

        total = float(b_order.get("total", 0.0) or 0.0)
        if existing:
            curr = existing[0]
            updated = self.mgr.update(
                "PEDIDOS",
                curr["ID"],
                {"TOTAL": total, "SUBTOTAL": total, "ID_EXT": ext_id},
            )
            return {"action": "UPDATED", "record": updated or curr}

        created = self.mgr.insert(
            "PEDIDOS",
            {
                "NUMERO": numero,
                "ID_CLIENTE": client_id,
                "DT_PEDIDO": str(b_order.get("data", "")).replace("-", "") or today_dbf(),
                "SUBTOTAL": total,
                "DESCONTO": 0.0,
                "FRETE": 0.0,
                "TOTAL": total,
                "SITUACAO": "APROVADO",
                "ORIGEM": "BLING",
                "ID_EXT": ext_id,
            },
        )
        return {"action": "CREATED", "record": created}

    def run_sync(self, scopes: List[str]) -> Dict[str, Any]:
        stats = {"products": 0, "contacts": 0, "orders": 0}
        try:
            if "products" in scopes or "all" in scopes:
                for p in fetch_bling_products(self.api):
                    self.upsert_bling_product(p)
                    stats["products"] += 1
            if "contacts" in scopes or "all" in scopes:
                for c in fetch_bling_contacts(self.api):
                    self.upsert_bling_client(c)
                    stats["contacts"] += 1
            if "orders" in scopes or "all" in scopes:
                for o in fetch_bling_orders(self.api):
                    self.upsert_bling_order(o)
                    stats["orders"] += 1

            total_synced = sum(stats.values())
            rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING")
            if rows:
                prev_total = int(rows[0].get("TOTAL_SYNC", 0))
                self.mgr.update(
                    "INTEGR",
                    rows[0]["ID"],
                    {
                        "SITUACAO": "CONECTADO",
                        "ULT_SYNC": now_iso(),
                        "STATUS_MSG": f"Sincronização concluída ({total_synced} registros processados).",
                        "TOTAL_SYNC": prev_total + total_synced,
                    },
                )
            return {"status": "SUCCESS", "synced": stats, "timestamp": now_iso()}
        except Exception as exc:
            rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING")
            if rows:
                self.mgr.update(
                    "INTEGR",
                    rows[0]["ID"],
                    {"SITUACAO": "ERRO", "STATUS_MSG": str(exc)[:200]},
                )
            self.notif.notify(
                "ERRO_SYNC",
                "Falha na sincronização com o Bling",
                str(exc)[:200],
                entidade="INTEGRACOES",
            )
            raise

