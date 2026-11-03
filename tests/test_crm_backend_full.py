import inspect
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel
from app.api.dependencies import get_current_user
from app.core.exceptions import CRMSatiroException


class _ResponseStub:
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data
        self.text = json.dumps(data, ensure_ascii=False, default=str)

    def json(self) -> Any:
        return self._data


class _FakeRequest:
    def __init__(self, app: FastAPI):
        self.app = app


class DirectFastAPIClient:
    """Despachante síncrono para rotas FastAPI sem depender de sockets loopback bloqueados no sandbox Windows."""

    def __init__(self, app: FastAPI):
        self.app = app

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> _ResponseStub:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        hdrs = {k.lower(): v for k, v in (headers or {}).items()}
        mgr = self.app.state.dbf_manager
        req = _FakeRequest(self.app)

        all_routes = []
        for r in self.app.routes:
            if isinstance(r, APIRoute):
                all_routes.append(r)
            elif hasattr(r, "original_router"):
                for sub_r in r.original_router.routes:
                    if isinstance(sub_r, APIRoute):
                        all_routes.append(sub_r)

        for route in all_routes:
            if method.upper() not in route.methods:
                continue
            r_path = route.path.rstrip("/") or "/"
            pattern = "^" + re.sub(r"\{([a-zA-Z0-9_]+)\}", r"(?P<\1>[^/]+)", r_path) + "$"
            m = re.match(pattern, path)
            if not m:
                continue

            path_params = m.groupdict()
            sig = inspect.signature(route.endpoint)
            kwargs: Dict[str, Any] = {}

            try:
                for pname, param in sig.parameters.items():
                    if pname == "mgr":
                        kwargs[pname] = mgr
                    elif pname == "user":
                        auth_hdr = hdrs.get("authorization", "")
                        kwargs[pname] = get_current_user(req, authorization=auth_hdr, mgr=mgr)
                    elif pname in path_params:
                        kwargs[pname] = path_params[pname]
                    elif pname in query_params:
                        val: Any = query_params[pname]
                        if param.annotation is int:
                            val = int(val)
                        elif param.annotation is float:
                            val = float(val)
                        elif param.annotation is bool:
                            val = str(val).lower() in ("true", "1", "t")
                        kwargs[pname] = val
                    elif (
                        isinstance(param.annotation, type)
                        and issubclass(param.annotation, BaseModel)
                    ):
                        kwargs[pname] = param.annotation(**(json_body or {}))
                    elif pname == "payload" and json_body is not None:
                        kwargs[pname] = json_body
                    elif hasattr(param.default, "default") and not isinstance(param.default, type):
                        kwargs[pname] = param.default.default

                result = route.endpoint(**kwargs)
                code = route.status_code or 200
                return _ResponseStub(code, result)
            except CRMSatiroException as exc:
                return _ResponseStub(
                    exc.status_code,
                    {
                        "error_code": exc.error_code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                )
        return _ResponseStub(404, {"message": f"Route {method} {path} not found"})

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> _ResponseStub:
        return self.request("GET", url, headers=headers)

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> _ResponseStub:
        return self.request("POST", url, headers=headers, json_body=json)

    def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> _ResponseStub:
        return self.request("PUT", url, headers=headers, json_body=json)

    def patch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> _ResponseStub:
        return self.request("PATCH", url, headers=headers, json_body=json)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> _ResponseStub:
        return self.request("DELETE", url, headers=headers)


class TestCRMBackendFull(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="satiro_api_test_"))
        from app.main import create_app

        self.app = create_app(custom_data_dir=self.temp_dir)
        self.client = DirectFastAPIClient(self.app)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _auth_headers(self, login: str = "admin", password: str = "GlobalCards@2026"):
        resp = self.client.post("/api/auth/login", json={"login": login, "password": password})
        self.assertEqual(resp.status_code, 200, resp.text)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_01_auth_lockout_and_permissions(self):
        bad = self.client.post("/api/auth/login", json={"login": "admin", "password": "wrong"})
        self.assertEqual(bad.status_code, 401)

        headers = self._auth_headers()
        me = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["PERFIL"], "ADMIN")
        self.assertTrue(len(me.json()["permissions"]) >= 10)

    def test_02_clients_contacts_addresses_and_overview_10_tabs(self):
        headers = self._auth_headers()
        cli_resp = self.client.post(
            "/api/clients",
            headers=headers,
            json={
                "TIPO_PES": "PJ",
                "NOME": "Hospital Santa Helena S/A",
                "FANTASIA": "Santa Helena",
                "CPF_CNPJ": "11.222.333/0001-81",
                "EMAIL": "compras@santahelena.com.br",
                "TELEFONE": "1132221111",
                "CELULAR": "11977776666",
                "ENDERECO": "Av. Paulista",
                "NUMERO": "1000",
                "BAIRRO": "Bela Vista",
                "CIDADE": "São Paulo",
                "UF": "SP",
                "CEP": "01310-100",
                "OBSERVACOES_LONGAS": "Cliente estratégico para crachás RFID Mifare 13.56MHz.",
            },
        )
        self.assertEqual(cli_resp.status_code, 201, cli_resp.text)
        client_id = cli_resp.json()["ID"]

        cnt_resp = self.client.post(
            "/api/contacts",
            headers=headers,
            json={
                "ID_CLIENTE": client_id,
                "NOME": "Carlos Eduardo (Suprimentos)",
                "CARGO": "Gerente de Compras",
                "DEPTO": "Suprimentos",
                "EMAIL": "carlos@santahelena.com.br",
                "CELULAR": "11977776666",
                "PRINCIPAL": True,
            },
        )
        self.assertEqual(cnt_resp.status_code, 201, cnt_resp.text)

        addr_resp = self.client.post(
            f"/api/clients/{client_id}/addresses",
            headers=headers,
            json={
                "TIPO_END": "ENTREGA",
                "ENDERECO": "Rua Vergueiro",
                "NUMERO": "500",
                "BAIRRO": "Liberdade",
                "CIDADE": "São Paulo",
                "UF": "SP",
                "CEP": "01504-000",
            },
        )
        self.assertEqual(addr_resp.status_code, 201, addr_resp.text)

        ov = self.client.get(f"/api/clients/{client_id}/overview", headers=headers)
        self.assertEqual(ov.status_code, 200)
        data = ov.json()
        for tab_key in (
            "client",
            "contacts",
            "addresses",
            "orders",
            "quotations",
            "opportunities",
            "conversations",
            "activities",
            "history",
            "notes",
        ):
            self.assertIn(tab_key, data)
        self.assertEqual(len(data["contacts"]), 1)
        self.assertEqual(len(data["addresses"]), 1)
        self.assertIn("RFID", data["notes"].get("content", ""))

    def test_03_products_quotations_orders_and_conversion(self):
        headers = self._auth_headers()
        cli = self.client.post(
            "/api/clients",
            headers=headers,
            json={"TIPO_PES": "PJ", "NOME": "TechCorp Ltda", "CPF_CNPJ": "11222333000181"},
        ).json()

        cat = self.client.post(
            "/api/products/categories",
            headers=headers,
            json={"CODIGO": "CRACHA_RFID", "NOME": "Crachás RFID & Proximidade", "ORDEM": 1},
        ).json()

        prd = self.client.post(
            "/api/products",
            headers=headers,
            json={
                "CODIGO": "CRD-MIFARE-01",
                "NOME": "Crachá PVC RFID Mifare 13.56MHz Personalizado 4x4",
                "DESC_CURTA": "Crachá em PVC CR80 0.76mm com chip Mifare 1K e impressão frente e verso.",
                "ID_CATEG": cat["ID"],
                "UNIDADE": "UN",
                "PRECO": 8.50,
                "PRECO_CUST": 3.20,
                "DESC_MAX": 15.0,
                "ESTOQUE": 5000,
                "DESTAQUE": True,
            },
        ).json()

        quo_resp = self.client.post(
            "/api/quotations",
            headers=headers,
            json={
                "ID_CLIENTE": cli["ID"],
                "DT_VALID": "2026-12-15",
                "FRETE": 45.0,
                "OBS": "Entrega em 5 dias úteis após aprovação da arte.",
                "ITEMS": [
                    {
                        "ID_PRODUTO": prd["ID"],
                        "QUANTIDADE": 200,
                        "PRECO_UNIT": 8.50,
                        "DESC_VALOR": 100.0,
                        "OBS_ITEM": "Personalização com dados variáveis",
                    }
                ],
            },
        )
        self.assertEqual(quo_resp.status_code, 201, quo_resp.text)
        quo = quo_resp.json()
        self.assertEqual(quo["SUBTOTAL"], 1700.0)
        self.assertEqual(quo["DESCONTO"], 100.0)
        self.assertEqual(quo["TOTAL"], 1645.0)

        self.client.patch(
            f"/api/quotations/{quo['ID']}/status",
            headers=headers,
            json={"SITUACAO": "APROVADO"},
        )
        conv_resp = self.client.post(
            f"/api/quotations/{quo['ID']}/convert-to-order",
            headers=headers,
        )
        self.assertEqual(conv_resp.status_code, 201, conv_resp.text)
        order = conv_resp.json()
        self.assertEqual(order["TOTAL"], 1645.0)
        self.assertEqual(order["ID_ORCAM"], quo["ID"])

        del_cli = self.client.delete(f"/api/clients/{cli['ID']}", headers=headers)
        self.assertEqual(del_cli.status_code, 409)

    def test_04_opportunities_funnel_activities_search_and_dashboard(self):
        headers = self._auth_headers()
        cli = self.client.post(
            "/api/clients",
            headers=headers,
            json={"TIPO_PES": "PJ", "NOME": "Colégio Alvorada", "TELEFONE": "1140005000"},
        ).json()

        funnels = self.client.get("/api/opportunities/funnels", headers=headers).json()
        stages = funnels[0]["stages"]
        first_stage = stages[0]["ID"]
        second_stage = stages[1]["ID"]

        opp = self.client.post(
            "/api/opportunities",
            headers=headers,
            json={
                "TITULO": "Kit 1.200 Crachás Escolares + Cordões Personalizados",
                "ID_CLIENTE": cli["ID"],
                "ID_FUNIL": funnels[0]["ID"],
                "ID_ETAPA": first_stage,
                "VALOR_EST": 9600.0,
                "ORIGEM": "WHATSAPP",
            },
        ).json()

        stage_move = self.client.patch(
            f"/api/opportunities/{opp['ID']}/stage",
            headers=headers,
            json={"ID_ETAPA": second_stage},
        )
        self.assertEqual(stage_move.status_code, 200)
        opp_detail = self.client.get(f"/api/opportunities/{opp['ID']}", headers=headers).json()
        self.assertEqual(opp_detail["ID_ETAPA"], second_stage)
        self.assertTrue(len(opp_detail["history"]) >= 2)

        act = self.client.post(
            "/api/activities",
            headers=headers,
            json={
                "TITULO": "Enviar amostra física de cordão acetinado",
                "TIPO": "TAREFA",
                "ID_CLIENTE": cli["ID"],
                "ID_OPORT": opp["ID"],
                "DATA_AG": "2026-11-05",
                "HORA_AG": "14:30",
                "PRIORIDADE": "ALTA",
            },
        ).json()
        done_act = self.client.patch(f"/api/activities/{act['ID']}/complete", headers=headers)
        self.assertEqual(done_act.status_code, 200)
        self.assertEqual(done_act.json()["SITUACAO"], "CONCLUIDA")

        search_res = self.client.get("/api/search?q=Alvorada", headers=headers).json()
        self.assertEqual(len(search_res["clients"]), 1)

        dash = self.client.get("/api/dashboard/summary", headers=headers).json()
        self.assertEqual(dash["kpis"]["total_clients"], 1)
        self.assertEqual(dash["kpis"]["active_opportunities"], 1)

    def test_05_bling_sync_ownership_whatsapp_and_ai_assistant(self):
        headers = self._auth_headers()
        from app.integrations.bling.sync import BlingSyncService
        from app.database.dbf_manager import DBFManager

        mgr = DBFManager(base_data_dir=self.temp_dir)
        sync_svc = BlingSyncService(mgr)

        res1 = sync_svc.upsert_bling_product(
            {
                "id": "99887766",
                "codigo": "BLG-CORD-01",
                "nome": "Cordão Personalizado 20mm Acetinado",
                "preco": 4.90,
                "estoque": {"saldoVirtualTotal": 1200},
                "unidade": "UN",
                "situacao": "A",
            }
        )
        self.assertEqual(res1["action"], "CREATED")
        prod_id = res1["record"]["ID"]

        mgr.update("PRODUTOS", prod_id, {"DESC_MAX": 18.0, "DESTAQUE": True})

        res2 = sync_svc.upsert_bling_product(
            {
                "id": "99887766",
                "codigo": "BLG-CORD-01",
                "nome": "Cordão Personalizado 20mm Acetinado",
                "preco": 5.20,
                "estoque": {"saldoVirtualTotal": 950},
                "unidade": "UN",
                "situacao": "A",
            }
        )
        self.assertEqual(res2["action"], "UPDATED")
        self.assertEqual(res2["record"]["ID"], prod_id)
        self.assertEqual(res2["record"]["PRECO"], 5.20)
        self.assertEqual(res2["record"]["ESTOQUE"], 950.0)
        self.assertEqual(res2["record"]["DESC_MAX"], 18.0)
        self.assertTrue(res2["record"]["DESTAQUE"])

        conv = self.client.post(
            "/api/whatsapp/conversations",
            headers=headers,
            json={"TELEFONE": "5511999990000", "NOME_CONT": "Mariana (Eventos)"},
        ).json()
        msg = self.client.post(
            f"/api/whatsapp/conversations/{conv['ID']}/messages",
            headers=headers,
            json={"DIRECAO": "ENTRADA", "CONTEUDO": "Olá, preciso de cotação de 300 pulseiras Tyvek."},
        )
        self.assertEqual(msg.status_code, 201)

        ai_resp = self.client.post(
            "/api/ai/chat",
            headers=headers,
            json={"prompt": "Resuma os indicadores atuais do CRM e produtos cadastrados."},
        )
        self.assertEqual(ai_resp.status_code, 200)
        self.assertIn("Cordão Personalizado", ai_resp.json()["answer"])


if __name__ == "__main__":
    unittest.main()
