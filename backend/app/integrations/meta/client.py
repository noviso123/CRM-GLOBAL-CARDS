from typing import Any, Dict
from app.database.dbf_manager import DBFManager
from app.integrations.meta.auth import MetaIntegrationAuth


class MetaGraphClient:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.auth = MetaIntegrationAuth(mgr)

    def get_status(self) -> Dict[str, Any]:
        rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "META")
        return rows[0] if rows else {"PROVEDOR": "META", "SITUACAO": "DESCONECTADO"}

