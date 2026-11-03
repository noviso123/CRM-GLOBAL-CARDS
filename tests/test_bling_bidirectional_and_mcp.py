import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.database.dbf_manager import DBFManager
from app.mcp.bling_mcp import BlingMCPEngine
from app.schemas.client import ClientCreate
from app.schemas.order import OrderCreate, OrderItemInput
from app.schemas.product import ProductCreate
from app.schemas.quotation import QuotationCreate, QuotationItemInput
from app.services.client_service import ClientService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.quotation_service import QuotationService


class TestBlingBidirectionalAndMCP(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="gc_bling_test_"))
        self.mgr = DBFManager(base_data_dir=self.test_dir)
        self.mgr.initialize_all_tables()

        self.prod_svc = ProductService(self.mgr)
        self.cli_svc = ClientService(self.mgr)
        self.order_svc = OrderService(self.mgr)
        self.quo_svc = QuotationService(self.mgr)
        self.mcp_engine = BlingMCPEngine(self.mgr)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_create_product_syncs_to_bling(self):
        prod = self.prod_svc.create_product(
            ProductCreate(
                CODIGO="PRD-CR-01",
                NOME="Cartão PVC Personalizado",
                PRECO=5.50,
                ESTOQUE=500,
                UNIDADE="UN",
                DESC_CURTA="Crachá em PVC",
            ),
            user_id="ADMIN_01",
        )
        self.assertTrue(prod["ID_EXT"].startswith("BLG-"))
        self.assertEqual(prod["ORIGEM"], "CRM_SYNC")

    def test_02_create_client_syncs_to_bling(self):
        cli = self.cli_svc.create_client(
            ClientCreate(
                TIPO_PES="PJ",
                NOME="Global Cards Corporativo",
                CPF_CNPJ="11.222.333/0001-81",
                EMAIL="contato@globalcards.com.br",
                TELEFONE="1133334444",
                CIDADE="São Paulo",
                UF="SP",
            ),
            user_id="ADMIN_01",
        )
        self.assertTrue(cli["ID_EXT"].startswith("BLG-"))

    def test_03_create_order_syncs_and_advances_status_in_bling(self):
        prod = self.prod_svc.create_product(
            ProductCreate(CODIGO="PRD-CORD", NOME="Cordão Roller", PRECO=3.0, ESTOQUE=100),
            user_id="ADMIN_01",
        )
        cli = self.cli_svc.create_client(
            ClientCreate(TIPO_PES="PF", NOME="Cliente Final", CPF_CNPJ="12345678909"),
            user_id="ADMIN_01",
        )
        order = self.order_svc.create_order(
            OrderCreate(
                ID_CLIENTE=cli["ID"],
                ITEMS=[OrderItemInput(ID_PRODUTO=prod["ID"], QUANTIDADE=10, PRECO_UNIT=3.0)],
            ),
            user_id="ADMIN_01",
        )
        self.assertTrue(order["ID_EXT"].startswith("BLG-"))

        # Avança a situação do pedido
        updated = self.order_svc.update_status(order["ID"], "FATURADO", user_id="ADMIN_01")
        self.assertEqual(updated["SITUACAO"], "FATURADO")

    def test_04_quotation_conversion_transmits_to_bling(self):
        prod = self.prod_svc.create_product(
            ProductCreate(CODIGO="PRD-ORC", NOME="Cartão Mifare 1K", PRECO=4.0, ESTOQUE=200),
            user_id="ADMIN_01",
        )
        cli = self.cli_svc.create_client(
            ClientCreate(TIPO_PES="PJ", NOME="Empresa Segura", CPF_CNPJ="11.222.333/0001-81"),
            user_id="ADMIN_01",
        )
        quo = self.quo_svc.create_quotation(
            QuotationCreate(
                ID_CLIENTE=cli["ID"],
                ITEMS=[QuotationItemInput(ID_PRODUTO=prod["ID"], QUANTIDADE=50, PRECO_UNIT=4.0)],
            ),
            user_id="ADMIN_01",
        )
        order = self.quo_svc.convert_to_order(quo["ID"], user_id="ADMIN_01")
        self.assertTrue(order["ID_EXT"].startswith("BLG-"))
        self.assertEqual(order["SITUACAO"], "APROVADO")

    def test_05_bling_mcp_engine_tools(self):
        defs = self.mcp_engine.get_tool_definitions()
        self.assertGreaterEqual(len(defs), 5)
        names = [d["name"] for d in defs]
        self.assertIn("bling_sincronizar_tudo", names)
        self.assertIn("bling_listar_pedidos", names)
        self.assertIn("bling_consultar_estoque", names)

        # Executa tool MCP
        res = self.mcp_engine.execute_tool("bling_consultar_estoque", {"codigo_ou_id": "Mifare"})
        self.assertIn("content", res)


if __name__ == "__main__":
    unittest.main()
