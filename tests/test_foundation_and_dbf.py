import unittest
import tempfile
import shutil
import threading
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))


class TestFoundationAndDBFEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="satiro_test_"))
        self.dbf_dir = self.temp_dir / "dbf"
        self.idx_dir = self.temp_dir / "indexes"
        self.doc_dir = self.temp_dir / "documents"
        self.att_dir = self.temp_dir / "attachments"
        self.bak_dir = self.temp_dir / "backups"
        self.lock_dir = self.temp_dir / "locks"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_identifiers_and_validators(self):
        from app.utils.identifiers import generate_id, generate_code
        from app.utils.validators import validate_cpf_cnpj, normalize_digits

        uid1 = generate_id()
        uid2 = generate_id()
        self.assertEqual(len(uid1), 36)
        self.assertNotEqual(uid1, uid2)
        self.assertEqual(generate_code("CLI", 42), "CLI-00042")
        self.assertTrue(validate_cpf_cnpj("52998224725"))  # CPF válido
        self.assertTrue(validate_cpf_cnpj("11.222.333/0001-81"))  # CNPJ válido
        self.assertFalse(validate_cpf_cnpj("111.111.111-11"))
        self.assertEqual(normalize_digits("11.222.333/0001-81"), "11222333000181")

    def test_02_initialize_all_21_dbf_tables(self):
        from app.database.dbf_manager import DBFManager
        from app.database.dbf_schema import ALL_TABLES

        self.assertEqual(len(ALL_TABLES), 21)
        mgr = DBFManager(base_data_dir=self.temp_dir)
        mgr.initialize_all_tables()

        for table_name in ALL_TABLES:
            dbf_path = self.dbf_dir / f"{table_name}.DBF"
            self.assertTrue(dbf_path.exists(), f"Missing {table_name}.DBF")
            with open(dbf_path, "rb") as f:
                header = f.read(32)
                self.assertEqual(header[0], 0x03)  # dBase III+

    def test_03_crud_accents_indexes_and_pack(self):
        from app.database.dbf_manager import DBFManager

        mgr = DBFManager(base_data_dir=self.temp_dir)
        mgr.initialize_all_tables()

        rec = mgr.insert(
            "CLIENTES",
            {
                "CODIGO": "CLI-00001",
                "TIPO_PES": "PJ",
                "NOME": "Gráfica São João & Crachás Corporativos S/A",
                "FANTASIA": "São João Identificação",
                "CPF_CNPJ": "11222333000181",
                "EMAIL": "contato@saojoao.com.br",
                "TELEFONE": "1133334444",
                "CELULAR": "11988887777",
                "CIDADE": "São Paulo",
                "UF": "SP",
                "PAIS": "Brasil",
                "SITUACAO": "ATIVO",
                "ORIGEM": "LOCAL",
            },
        )
        self.assertIn("ID", rec)
        self.assertEqual(rec["VERSAO"], 1)

        # Busca indexada O(1) por ID e por CPF_CNPJ
        fetched = mgr.get_by_id("CLIENTES", rec["ID"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["NOME"], "Gráfica São João & Crachás Corporativos S/A")

        by_doc = mgr.find_by_field("CLIENTES", "CPF_CNPJ", "11222333000181")
        self.assertEqual(len(by_doc), 1)
        self.assertEqual(by_doc[0]["ID"], rec["ID"])

        # Atualização com incremento de versão
        updated = mgr.update("CLIENTES", rec["ID"], {"FANTASIA": "São João Crachás VIP"})
        self.assertEqual(updated["FANTASIA"], "São João Crachás VIP")
        self.assertEqual(updated["VERSAO"], 2)

        # Exclusão lógica e compactação física (PACK)
        deleted = mgr.delete("CLIENTES", rec["ID"])
        self.assertTrue(deleted)
        self.assertIsNone(mgr.get_by_id("CLIENTES", rec["ID"]))

        pack_stats = mgr.pack_table("CLIENTES")
        self.assertEqual(pack_stats["active_records"], 0)
        self.assertEqual(pack_stats["removed_records"], 1)

    def test_04_concurrent_writes_and_referential_integrity(self):
        from app.database.dbf_manager import DBFManager
        from app.database.integrity import IntegrityValidator
        from app.core.exceptions import IntegrityErrorCRM

        mgr = DBFManager(base_data_dir=self.temp_dir)
        mgr.initialize_all_tables()
        validator = IntegrityValidator(mgr)

        # Inserção concorrente com 8 threads
        errors = []

        def worker(idx: int):
            try:
                mgr.insert(
                    "CATEGORIAS",
                    {
                        "CODIGO": f"CAT-{idx:03d}",
                        "NOME": f"Categoria Concorrente {idx}",
                        "ORDEM": idx,
                        "SITUACAO": "ATIVO",
                        "ORIGEM": "LOCAL",
                    },
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, 9)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        cats = mgr.find_all("CATEGORIAS")
        self.assertEqual(len(cats), 8)

        # Integridade referencial: impedir contato para cliente inexistente
        with self.assertRaises(IntegrityErrorCRM):
            validator.validate_contact_insert({"ID_CLIENTE": "inexistente", "NOME": "João"})

    def test_05_backup_and_restore_with_sha256_manifest(self):
        from app.database.dbf_manager import DBFManager
        from app.database.backup import BackupManager

        mgr = DBFManager(base_data_dir=self.temp_dir)
        mgr.initialize_all_tables()
        bak = BackupManager(mgr)

        cli = mgr.insert(
            "CLIENTES",
            {
                "CODIGO": "CLI-00999",
                "TIPO_PES": "PF",
                "NOME": "Maria da Conceição Oliveira",
                "CPF_CNPJ": "52998224725",
                "PAIS": "Brasil",
                "SITUACAO": "ATIVO",
                "ORIGEM": "LOCAL",
            },
        )

        backup_info = bak.create_backup(description="Teste Fase 2")
        self.assertTrue(Path(backup_info["zip_path"]).exists())
        self.assertEqual(backup_info["tables_count"], 21)

        # Exclui o cliente e restaura o backup
        mgr.delete("CLIENTES", cli["ID"])
        self.assertIsNone(mgr.get_by_id("CLIENTES", cli["ID"]))

        restore_info = bak.restore_backup(backup_info["backup_id"])
        self.assertTrue(restore_info["restored"])

        restored_cli = mgr.get_by_id("CLIENTES", cli["ID"])
        self.assertIsNotNone(restored_cli)
        self.assertEqual(restored_cli["NOME"], "Maria da Conceição Oliveira")


if __name__ == "__main__":
    unittest.main()

