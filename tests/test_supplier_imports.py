import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from app.core.security import hash_password
from app.database.dbf_manager import DBFManager
from app.database.migrations import run_startup_migrations
from app.integrations.suppliers.service import SupplierScraper, SupplierService
from app.main import create_app
from tests.test_crm_backend_full import DirectFastAPIClient


class TestSupplierImports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="crm_suppliers_test_")
        cls.mgr = DBFManager(base_data_dir=Path(cls.temp_dir))
        run_startup_migrations(cls.mgr, hash_password)
        cls.svc = SupplierService(cls.mgr)

        cls.app = create_app(custom_data_dir=Path(cls.temp_dir))
        cls.client = DirectFastAPIClient(cls.app)

        login_resp = cls.client.post(
            "/api/auth/login",
            json={"login": "admin", "password": "GlobalCards@2026"},
        )
        data = login_resp.json()
        token = data.get("access_token")
        cls.auth_headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_suppliers_partners_list(self):
        resp = self.client.get("/api/suppliers/partners", headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        partners = resp.json()
        self.assertEqual(len(partners), 4)
        ids = [p["id"] for p in partners]
        self.assertIn("ATUAL_CARD", ids)
        self.assertIn("ZAP_GRAFICA", ids)
        self.assertIn("FUTURA_IM", ids)
        self.assertIn("PADRAO_COLOR", ids)

    def test_02_catalog_search_and_filters(self):
        resp = self.client.get("/api/suppliers/catalog?q=cracha", headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        crachas = resp.json()
        self.assertGreaterEqual(len(crachas), 2)

        # Filtro por fornecedor Zap Gráfica
        resp_zap = self.client.get("/api/suppliers/catalog?supplier=ZAP_GRAFICA", headers=self.auth_headers)
        self.assertEqual(resp_zap.status_code, 200)
        zap_items = resp_zap.json()
        self.assertGreaterEqual(len(zap_items), 2)
        for item in zap_items:
            self.assertEqual(item["fornecedor_id"], "ZAP_GRAFICA")

    def test_03_extract_from_supplier_urls(self):
        # URL Atual Card
        resp = self.client.post(
            "/api/suppliers/extract-url",
            json={"url": "https://www.atualcard.com.br/produto/cracha-pvc-076mm"},
            headers=self.auth_headers,
        )
        self.assertEqual(resp.status_code, 200)
        res_atual = resp.json()
        self.assertEqual(res_atual["fornecedor_id"], "ATUAL_CARD")
        self.assertGreater(res_atual["preco_custo_estimado"], 0)
        self.assertGreater(res_atual["preco_venda_sugerido"], res_atual["preco_custo_estimado"])

    def test_04_import_product_unit_mode_and_bling_sync(self):
        payload = {
            "fornecedor_id": "ATUAL_CARD",
            "fornecedor_nome": "Atual Card",
            "nome": "Crachá PVC Empresarial Teste Unitário",
            "sku": "ATU-TESTE-01",
            "categoria": "Crachás & Identificação",
            "modo_venda": "UN",
            "lote_quantidade": 1,
            "preco_custo": 4.50,
            "preco_venda": 11.90,
            "estoque_inicial": 80.0,
            "estoque_minimo": 15.0,
            "imagem": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f",
            "descricao": "Crachá de teste importado do fornecedor.",
            "especificacoes": {"Material": "PVC 0.76mm", "Formato": "54x86mm"},
            "url_origem": "https://www.atualcard.com.br/produto/cracha-pvc-076mm",
        }

        resp = self.client.post("/api/suppliers/import", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 201)
        res = resp.json()
        self.assertTrue(res["success"])
        self.assertEqual(res["product"]["NOME"], "Crachá PVC Empresarial Teste Unitário")
        self.assertEqual(res["product"]["UNIDADE"], "UN")
        self.assertEqual(float(res["product"]["PRECO"]), 11.90)
        self.assertEqual(float(res["product"]["ESTOQUE"]), 80.0)
        self.assertTrue(res["bling_synced"])

    def test_05_import_product_batch_mode(self):
        payload = {
            "fornecedor_id": "ZAP_GRAFICA",
            "fornecedor_nome": "Zap Gráfica",
            "nome": "Cordão para Crachá 20mm (Pacote com 100 un)",
            "sku": "ZAP-COR-100UN",
            "categoria": "Cordões & Acessórios",
            "modo_venda": "LOTE",
            "lote_quantidade": 100,
            "preco_custo": 280.00,
            "preco_venda": 599.00,
            "estoque_inicial": 5.0,  # 5 pacotes de 100
            "estoque_minimo": 1.0,
            "imagem": "https://images.unsplash.com/photo-1590402494682-cd3fb53b1f70",
            "descricao": "Pacote fechado com 100 cordões personalizados.",
            "especificacoes": {"Quantidade no Lote": "100 unidades", "Largura": "20mm"},
        }

        resp = self.client.post("/api/suppliers/import", json=payload, headers=self.auth_headers)
        self.assertEqual(resp.status_code, 201)
        res = resp.json()
        self.assertTrue(res["success"])
        self.assertEqual(res["product"]["UNIDADE"], "LOTE-100")
        self.assertEqual(float(res["product"]["PRECO"]), 599.00)
        self.assertEqual(float(res["product"]["ESTOQUE"]), 5.0)


if __name__ == "__main__":
    unittest.main()
