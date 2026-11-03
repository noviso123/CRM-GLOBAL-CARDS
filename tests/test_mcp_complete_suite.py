import sys
import unittest
import tempfile
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.dbf_manager import DBFManager
from app.mcp.bling_mcp import BlingMCPEngine


class TestMCPCompleteSuite(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="mcp_test_"))
        self.mgr = DBFManager(base_data_dir=self.tmp_dir)
        self.mgr.initialize_all_tables()
        self.engine = BlingMCPEngine(self.mgr)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_mcp_tool_definitions_and_categories(self):
        tools = self.engine.get_tool_definitions()
        self.assertGreaterEqual(len(tools), 32)

        categories = set(t.get("category") for t in tools)
        expected_categories = {
            "Bling ERP",
            "WhatsApp & Meta",
            "Fornecedores Gráficos",
            "CRM Comercial",
            "BI & Métricas",
        }
        self.assertTrue(expected_categories.issubset(categories))

        for t in tools:
            self.assertTrue(t.get("name"))
            self.assertTrue(t.get("description"))
            self.assertIsInstance(t.get("inputSchema"), dict)

    def test_mcp_all_35_tools_execute_cleanly(self):
        tools = self.engine.get_tool_definitions()
        self.assertEqual(len(tools), 35)
        for t in tools:
            name = t["name"]
            res = self.engine.execute_tool(name, {})
            self.assertIsInstance(res, dict, f"Tool {name} did not return dict")
            self.assertIn("content", res, f"Tool {name} missing content")
            self.assertIsInstance(res["content"], list)
            self.assertGreater(len(res["content"]), 0)
            self.assertEqual(res["content"][0].get("type"), "text")

    def test_mcp_resources_and_prompts(self):
        resources = self.engine.get_resource_definitions()
        self.assertGreaterEqual(len(resources), 5)
        for r in resources:
            self.assertIn("uri", r)
            self.assertIn("name", r)
            res_data = self.engine.read_resource(r["uri"])
            self.assertIn("uri", res_data)
            self.assertIn("text", res_data)

        prompts = self.engine.get_prompt_definitions()
        self.assertGreaterEqual(len(prompts), 4)
        for p in prompts:
            self.assertIn("name", p)
            self.assertIn("description", p)

    def test_mcp_jsonrpc_protocol_flow(self):
        # 1. initialize
        init_res = self.engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "crm-global-cards-mcp")

        # 2. tools/list
        tools_res = self.engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertEqual(len(tools_res["result"]["tools"]), 35)

        # 3. tools/call
        call_res = self.engine.handle_jsonrpc({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "fornecedores_listar_parceiros", "arguments": {}}
        })
        self.assertIn("fornecedores", call_res["result"])

        # 4. resources/list
        res_list = self.engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}})
        self.assertGreaterEqual(len(res_list["result"]["resources"]), 5)

        # 5. ping
        ping_res = self.engine.handle_jsonrpc({"jsonrpc": "2.0", "id": 5, "method": "ping", "params": {}})
        self.assertIn("result", ping_res)


if __name__ == "__main__":
    unittest.main()
