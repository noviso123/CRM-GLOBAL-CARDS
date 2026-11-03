import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR / "tests"))

from app.core.security import create_access_token
from app.main import create_app
from test_crm_backend_full import DirectFastAPIClient


class TestMandatoryScenariosSec33(unittest.TestCase):
    """Cobre os cenários adicionais da Seção 33 (Segurança, RBAC, Alçada de Desconto, Falha de Rede Bling, Relatórios, IA e Diagnósticos)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = Path(tempfile.mkdtemp(prefix="satiro_sec33_test_"))
        cls.app = create_app(custom_data_dir=cls.tmp_dir)
        cls.client = DirectFastAPIClient(cls.app)

        res = cls.client.post("/api/auth/login", json={"login": "admin", "password": "GlobalCards@2026"})
        assert res.status_code == 200, res.text
        cls.admin_token = res.json()["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_expired_and_invalid_tokens_rejected(self) -> None:
        expired_token = create_access_token(
            subject="any-id",
            extra_claims={"login": "admin", "perfil": "ADMIN"},
            expires_minutes=-10,
        )
        res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(res.status_code, 401)

        res2 = self.client.get("/api/clients")
        self.assertEqual(res2.status_code, 401)

    def test_02_rbac_permission_denial_and_discount_limit(self) -> None:
        u_res = self.client.post(
            "/api/settings/users",
            headers=self.admin_headers,
            json={
                "NOME": "Atendente Teste",
                "LOGIN": "atendente1",
                "EMAIL": "atend@satiro.local",
                "PASSWORD": "SenhaUser123",
                "PERFIL": "ATENDIMENTO",
                "CARGO": "SAC",
                "DESC_MAX": 5.0,
            },
        )
        self.assertEqual(u_res.status_code, 201, u_res.text)

        login_res = self.client.post(
            "/api/auth/login",
            json={"login": "atendente1", "password": "SenhaUser123"},
        )
        self.assertEqual(login_res.status_code, 200, login_res.text)
        user_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        # Tenta acessar configurações administrativas de criação de usuário -> 403 Forbidden
        forbidden_res = self.client.post(
            "/api/settings/users",
            headers=user_headers,
            json={
                "NOME": "Outro",
                "LOGIN": "outro",
                "EMAIL": "o@satiro.local",
                "PASSWORD": "123",
                "PERFIL": "ADMIN",
            },
        )
        self.assertEqual(forbidden_res.status_code, 403)

        # Cria cliente e produto com admin para testar alçada de desconto no orçamento
        c_res = self.client.post(
            "/api/clients",
            headers=self.admin_headers,
            json={"TIPO_PES": "PF", "NOME": "Cliente Desconto", "CPF_CNPJ": "52998224725"},
        )
        self.assertEqual(c_res.status_code, 201, c_res.text)
        client_id = c_res.json()["ID"]

        p_res = self.client.post(
            "/api/products",
            headers=self.admin_headers,
            json={"NOME": "Cartão Mifare 1K", "PRECO": 100.0, "DESC_MAX": 8.0, "ESTOQUE": 50},
        )
        self.assertEqual(p_res.status_code, 201, p_res.text)
        prod_id = p_res.json()["ID"]

        # Usuário com alçada de 5% aplica 20% de desconto -> AUT_DESC fica False exigindo aprovação gerencial
        q_res = self.client.post(
            "/api/quotations",
            headers=user_headers,
            json={
                "ID_CLIENTE": client_id,
                "DESCONTO_EXTRA": 20.0,
                "ITEMS": [
                    {
                        "ID_PRODUTO": prod_id,
                        "QUANTIDADE": 1,
                        "PRECO_UNIT": 100.0,
                        "DESC_VALOR": 0.0,
                    }
                ],
            },
        )
        self.assertEqual(q_res.status_code, 201, q_res.text)
        self.assertFalse(q_res.json()["AUT_DESC"])

        # Desconto maior que valor bruto do item -> bloqueado com 400 ValidationErrorCRM
        q_invalid = self.client.post(
            "/api/quotations",
            headers=user_headers,
            json={
                "ID_CLIENTE": client_id,
                "ITEMS": [
                    {
                        "ID_PRODUTO": prod_id,
                        "QUANTIDADE": 1,
                        "PRECO_UNIT": 100.0,
                        "DESC_VALOR": 150.0,
                    }
                ],
            },
        )
        self.assertEqual(q_invalid.status_code, 422)

    def test_03_bling_offline_sync_graceful_handling(self) -> None:
        # Sem credenciais externas configuradas, retorna erro controlado 400 e registra status ERRO em INTEGR.DBF sem derrubar o CRM
        sync_res = self.client.post(
            "/api/integrations/bling/sync",
            headers=self.admin_headers,
            json={"scopes": ["products"]},
        )
        self.assertEqual(sync_res.status_code, 400)
        st_res = self.client.get("/api/integrations/status", headers=self.admin_headers)
        self.assertEqual(st_res.status_code, 200)
        bling_row = [r for r in st_res.json() if r["PROVEDOR"] == "BLING"][0]
        self.assertEqual(bling_row["SITUACAO"], "ERRO")

    def test_04_reports_ai_and_dbf_diagnostics_endpoints(self) -> None:
        rep = self.client.get("/api/reports/sales", headers=self.admin_headers)
        self.assertEqual(rep.status_code, 200)
        self.assertEqual(rep.json()["report_type"], "sales")

        diag = self.client.get("/api/settings/diagnostics/verify-dbf", headers=self.admin_headers)
        self.assertEqual(diag.status_code, 200)
        self.assertEqual(diag.json()["tables_count"], 21)
        self.assertFalse(diag.json()["sql_dependencies"])

        reb = self.client.post("/api/settings/diagnostics/rebuild-indexes", headers=self.admin_headers)
        self.assertEqual(reb.status_code, 200)
        self.assertEqual(reb.json()["status"], "REBUILT")

        bkp = self.client.post(
            "/api/settings/backup/create",
            headers=self.admin_headers,
            json={"description": "Teste automatizado Sec 33"},
        )
        self.assertEqual(bkp.status_code, 201)
        backup_id = bkp.json()["backup_id"]

        bkp_list = self.client.get("/api/settings/backup/list", headers=self.admin_headers)
        self.assertEqual(bkp_list.status_code, 200)
        self.assertTrue(any(b["backup_id"] == backup_id for b in bkp_list.json()))

        ai_res = self.client.post(
            "/api/ai/chat",
            headers=self.admin_headers,
            json={"prompt": "Gerar diagnóstico executivo de vendas"},
        )
        self.assertEqual(ai_res.status_code, 200)
        self.assertIn("Análise Comercial CRM GLOBAL CARDS", ai_res.json()["answer"])


if __name__ == "__main__":
    unittest.main()
