import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.database.dbf_manager import DBFManager
from app.integrations.meta.oauth import MetaOAuthManager
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.integrations.whatsapp.messages import WhatsAppService
from app.integrations.whatsapp.webhooks import handle_whatsapp_webhook
from app.main import create_app
from tests.test_crm_backend_full import DirectFastAPIClient


class TestWhatsAppMetaIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="gc_wa_meta_test_"))
        self.app = create_app(custom_data_dir=self.test_dir)
        self.mgr = self.app.state.dbf_manager

        self.wa_client = WhatsAppCloudClient(self.mgr)
        self.meta_oauth = MetaOAuthManager(self.mgr)
        self.wa_svc = WhatsAppService(self.mgr)
        self.client = DirectFastAPIClient(self.app)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _auth_headers(self, login: str = "admin", password: str = "GlobalCards@2026"):
        resp = self.client.post("/api/auth/login", json={"login": login, "password": password})
        self.assertEqual(resp.status_code, 200, resp.text)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_01_meta_oauth_url_and_fast_connect(self):
        """Valida geração de URL OAuth da Meta e conexão expressa em 1-clique."""
        url = self.meta_oauth.get_meta_authorize_url()
        self.assertTrue("facebook.com" in url or "login-screen" in url)
        if "facebook.com" in url:
            self.assertIn("whatsapp_business_messaging", url)

        # Executa Fast-Connect 1-Clique
        res = self.meta_oauth.fast_connect_whatsapp(
            phone_number="5511987654321", display_name="Global Cards Atendimento Oficial"
        )
        self.assertEqual(res["status"], "CONECTADO")
        self.assertIn("+55 (11)", res["display_phone_number"])

        # Confere status da conta
        acc = self.wa_client.get_account_status()
        self.assertTrue(acc["is_connected"])
        self.assertEqual(acc["quality_rating"], "GREEN")

    def test_02_meta_webhook_challenge_get_and_post(self):
        """Valida rota de verificação GET do webhook (Meta Challenge) e recebimento POST."""
        self.wa_client.save_config(
            phone_number_id="PHONE_123",
            access_token="TOKEN_ABC",
            verify_token="globalcards_wa_verify",
            display_phone_number="+55 11 99999-8888",
        )

        # 1. Simula GET da Meta para verificar Webhook
        resp_get = self.client.get(
            "/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=88291029&hub.verify_token=globalcards_wa_verify"
        )
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.text, "88291029")

        # 2. Simula GET com token incorreto
        resp_bad = self.client.get(
            "/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=88291029&hub.verify_token=token_errado"
        )
        self.assertEqual(resp_bad.status_code, 403)

        # 3. Simula POST de mensagem recebida da Meta
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "contacts": [{"profile": {"name": "Carlos Comprador"}}],
                                "messages": [
                                    {
                                        "from": "5511977776666",
                                        "id": "wamid.HBgLTEST12345",
                                        "type": "text",
                                        "text": {"body": "Gostaria de cotar 1000 cordões para crachá"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        resp_post = self.client.post("/api/whatsapp/webhook", json=payload)
        self.assertEqual(resp_post.status_code, 200)
        self.assertEqual(resp_post.json()["messages_received"], 1)

        # Verifica se conversa foi gravada no DBF
        convs = self.mgr.find_by_field("CONVERS", "TELEFONE", "5511977776666")
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["NOME_CONT"], "Carlos Comprador")

    def test_03_templates_meta_listing_and_sending(self):
        """Valida catálogo de templates HSM oficiais e envio em conversa ativa."""
        headers = self._auth_headers()

        # Cria conversa
        conv = self.wa_svc.create_or_get_conversation(
            telefone="5511988887777", nome_cont="Julia Eventos"
        )

        # Lista templates
        templates = self.client.get("/api/whatsapp/templates", headers=headers).json()
        self.assertGreaterEqual(len(templates), 4)
        names = [t["name"] for t in templates]
        self.assertIn("confirmacao_pedido", names)
        self.assertIn("pedido_faturado", names)
        self.assertIn("cobranca_pix", names)

        # Dispara template
        send_res = self.client.post(
            f"/api/whatsapp/conversations/{conv['ID']}/send-template",
            headers=headers,
            json={
                "template_name": "confirmacao_pedido",
                "parameters": ["Julia Eventos", "PED-00042", "1.250,00"],
            },
        )
        self.assertEqual(send_res.status_code, 201)
        self.assertEqual(send_res.json()["template"], "confirmacao_pedido")

        # Verifica histórico de mensagens da conversa
        msgs = self.wa_svc.list_messages(conv["ID"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["TIPO_MSG"], "TEMPLATE")
        self.assertIn("confirmacao_pedido", msgs[0]["CONTEUDO"])

    def test_04_api_fast_connect_and_test_send(self):
        """Valida endpoint /api/whatsapp/fast-connect e /api/whatsapp/test-send."""
        headers = self._auth_headers()

        fc_resp = self.client.post(
            "/api/whatsapp/fast-connect",
            headers=headers,
            json={
                "phone_number": "5511999990000",
                "display_name": "Global Cards Linha Matriz",
            },
        )
        self.assertEqual(fc_resp.status_code, 200)
        self.assertEqual(fc_resp.json()["status"], "CONECTADO")

        ts_resp = self.client.post(
            "/api/whatsapp/test-send",
            headers=headers,
            json={
                "to_phone": "5511999990000",
                "message": "Mensagem de teste unitário Meta Cloud",
            },
        )
        self.assertEqual(ts_resp.status_code, 200)
        self.assertEqual(ts_resp.json()["status"], "SENT")


if __name__ == "__main__":
    unittest.main()
