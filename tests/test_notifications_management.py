import unittest
import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.dbf_manager import DBFManager
from app.services.notification_service import NotificationService

class TestNotificationManagement(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("data_test_notif")
        self.mgr = DBFManager(base_data_dir=self.test_dir)
        self.service = NotificationService(self.mgr)

    def tearDown(self):
        del self.mgr
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_read_delete_and_clear_notifications(self):
        # 1. Cria 3 notificações
        n1 = self.service.notify("PEDIDO", "Novo Pedido #1", "Cliente A comprou", id_usu_dst="TODOS")
        n2 = self.service.notify("BLING", "Sync Concluído", "50 produtos sincronizados", id_usu_dst="TODOS")
        n3 = self.service.notify("ALERTA", "Estoque Baixo", "Produto X com estoque baixo", id_usu_dst="TODOS")

        all_notifs = self.service.list_notifications(user_id="U1", unread_only=False)
        self.assertEqual(len(all_notifs), 3)

        unread_notifs = self.service.list_notifications(user_id="U1", unread_only=True)
        self.assertEqual(len(unread_notifs), 3)

        # 2. Marca 1 como lida
        res_read = self.service.mark_read(n1["ID"])
        self.assertTrue(res_read["LIDA"])

        unread_after_read = self.service.list_notifications(user_id="U1", unread_only=True)
        self.assertEqual(len(unread_after_read), 2)

        # 3. Exclui notificação individual (n2)
        deleted = self.service.delete_notification(n2["ID"])
        self.assertTrue(deleted)

        remaining = self.service.list_notifications(user_id="U1", unread_only=False)
        self.assertEqual(len(remaining), 2)
        remaining_ids = [r["ID"] for r in remaining]
        self.assertNotIn(n2["ID"], remaining_ids)

        # 4. Limpa todas as notificações
        cleared = self.service.clear_all(user_id="U1")
        self.assertEqual(cleared, 2)

        final_notifs = self.service.list_notifications(user_id="U1", unread_only=False)
        self.assertEqual(len(final_notifs), 0)

if __name__ == "__main__":
    unittest.main()
