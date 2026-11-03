from typing import Any, Dict, List
from app.database.dbf_manager import DBFManager
from app.utils.validators import normalize_digits


class SearchService:
    """Pesquisa global rápida utilizando índices secundários .IDX antes de filtragem textual complementar."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr

    def global_search(self, query: str, limit_per_group: int = 8) -> Dict[str, List[Dict[str, Any]]]:
        q = (query or "").strip()
        if not q:
            return {
                "clients": [],
                "contacts": [],
                "products": [],
                "orders": [],
                "quotations": [],
                "opportunities": [],
                "activities": [],
                "conversations": [],
            }

        q_up = q.upper()
        q_digits = normalize_digits(q)

        # 1. Busca direta nos índices .IDX por código, documento, ID ou número
        exact_clients = (
            self.mgr.find_by_field("CLIENTES", "CODIGO", q_up)
            + (self.mgr.find_by_field("CLIENTES", "CPF_CNPJ", q_digits) if q_digits else [])
            + self.mgr.find_by_field("CLIENTES", "ID", q)
        )
        exact_ids = {c["ID"] for c in exact_clients}

        def match_records(table: str, fields: tuple[str, ...], prefound: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            results = list(prefound or [])
            seen = {r["ID"] for r in results}
            for rec in self.mgr.find_all(table):
                if rec["ID"] in seen:
                    continue
                for f in fields:
                    val = str(rec.get(f, "")).upper()
                    if q_up in val or (q_digits and len(q_digits) >= 4 and q_digits in val):
                        results.append(rec)
                        seen.add(rec["ID"])
                        break
                if len(results) >= limit_per_group:
                    break
            return results[:limit_per_group]

        return {
            "clients": match_records(
                "CLIENTES",
                ("CODIGO", "NOME", "FANTASIA", "CPF_CNPJ", "EMAIL", "TELEFONE", "CELULAR"),
                exact_clients,
            ),
            "contacts": match_records(
                "CONTATOS", ("NOME", "CARGO", "EMAIL", "TELEFONE", "CELULAR")
            ),
            "products": match_records(
                "PRODUTOS",
                ("CODIGO", "NOME", "DESC_CURTA"),
                self.mgr.find_by_field("PRODUTOS", "CODIGO", q_up),
            ),
            "orders": match_records(
                "PEDIDOS",
                ("NUMERO", "OBS", "ID_EXT"),
                self.mgr.find_by_field("PEDIDOS", "NUMERO", q_up),
            ),
            "quotations": match_records(
                "ORCAMENT",
                ("NUMERO", "OBS"),
                self.mgr.find_by_field("ORCAMENT", "NUMERO", q_up),
            ),
            "opportunities": match_records("OPORTUN", ("TITULO", "OBS", "ORIGEM")),
            "activities": match_records("ATIVIDAD", ("TITULO", "DESCRICAO", "TIPO")),
            "conversations": match_records("CONVERS", ("NOME_CONT", "TELEFONE", "ULT_MSG")),
        }

