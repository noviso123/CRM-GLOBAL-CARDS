import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from app.database.dbf_manager import DBFManager
from app.integrations.sync_orchestrator import SyncOrchestrator
from app.mcp.bling_mcp import BlingMCPEngine
from app.schemas.client import ClientCreate
from app.schemas.product import ProductCreate
from app.schemas.order import OrderCreate, OrderItemInput
from app.services.client_service import ClientService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.main import create_app
from tests.test_crm_backend_full import DirectFastAPIClient


class TestFullOmnidirectionalSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="gc_omni_sync_test_"))
        self.app = create_app(custom_data_dir=self.test_dir)
        self.mgr = self.app.state.dbf_manager

        self.orchestrator = SyncOrchestrator(self.mgr)
        self.mcp_engine = BlingMCPEngine(self.mgr)
        self.prod_svc = ProductService(self.mgr)
        self.cli_svc = ClientService(self.mgr)
        self.order_svc = OrderService(self.mgr)
        self.client = DirectFastAPIClient(self.app)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _auth_headers(self, login: str = "admin", password: str = "GlobalCards@2026"):
        resp = self.client.post("/api/auth/login", json={"login": login, "password": password})
        self.assertEqual(resp.status_code, 200, resp.text)
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_01_mcp_engine_catalog_and_jsonrpc(self):
        """Valida catálogo de 16+ tools, resources e protocolo JSON-RPC 2.0 oficial."""
        tools = self.mcp_engine.get_tool_definitions()
        self.assertGreaterEqual(len(tools), 16)

        categories = set(t.get("category") for t in tools)
        self.assertIn("Bling ERP", categories)
        self.assertIn("WhatsApp & Meta", categories)
        self.assertIn("CRM Comercial", categories)
        self.assertIn("BI & Métricas", categories)

        # Testa JSON-RPC initialize
        init_res = self.mcp_engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_res["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "crm-global-cards-mcp")

        # Testa JSON-RPC tools/list
        tl_res = self.mcp_engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertGreaterEqual(len(tl_res["result"]["tools"]), 16)

        # Testa JSON-RPC resources/list
        res_list = self.mcp_engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
        self.assertGreaterEqual(len(res_list["result"]["resources"]), 3)

    def test_02_bidirectional_sync_inbound_outbound_and_whatsapp(self):
        """Valida sincronização 100% total: CRM -> Bling, Bling -> CRM e cruzamento WhatsApp."""
        # 1. Cria produto e cliente no CRM sem ID externo
        prod = self.prod_svc.create_product(
            ProductCreate(CODIGO="PRD-CORD-LUXO", NOME="Cordão Acetinado 20mm Presilha", PRECO=6.50, ESTOQUE=800),
            user_id="ADMIN_01",
        )
        cli = self.cli_svc.create_client(
            ClientCreate(TIPO_PES="PJ", NOME="Eventos Brasil Corp", CPF_CNPJ="11.222.333/0001-81", CELULAR="5511999887766"),
            user_id="ADMIN_01",
        )

        # 2. Cria conversa no WhatsApp sem vínculo prévio
        conv = self.mgr.insert(
            "CONVERS",
            {
                "TELEFONE": "5511999887766",
                "NOME_CONT": "Contato Eventos Brasil",
                "ID_CLIENTE": "",
                "SITUACAO": "EM_ATENDIMENTO",
                "NAO_LIDAS": 1,
            },
        )
        self.assertEqual(conv.get("ID_CLIENTE"), "")

        # 3. Executa a sincronização 100% completa
        result = self.orchestrator.run_full_bidirectional_sync()
        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreaterEqual(result["total_records_processed"], 1)

        # 4. Confere se a conversa de WhatsApp foi auto-vinculada com o cliente!
        conv_updated = self.mgr.get_by_id("CONVERS", conv["ID"])
        self.assertEqual(conv_updated["ID_CLIENTE"], cli["ID"])

    def test_03_api_endpoint_full_sync_omnidirectional(self):
        """Valida chamada ao endpoint /api/integrations/full-sync-omnidirectional via HTTP."""
        headers = self._auth_headers()
        resp = self.client.post("/api/integrations/full-sync-omnidirectional", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("inbound_from_bling", data)
        self.assertIn("outbound_to_bling", data)
        self.assertIn("cross_channel_whatsapp", data)


if __name__ == "__main__":
    unittest.main()

