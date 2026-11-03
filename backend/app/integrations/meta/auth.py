import json
from typing import Any, Dict
from app.core.security import decrypt_secret_payload, encrypt_secret_payload
from app.database.dbf_manager import DBFManager
from app.utils.dates import now_iso


class MetaIntegrationAuth:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.secrets_dir = self.mgr.documents_dir / "secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, app_id: str, app_secret: str, business_id: str = "") -> Dict[str, Any]:
        sf = self.secrets_dir / "meta_graph.enc"
        sf.write_text(
            encrypt_secret_payload(
                json.dumps(
                    {"app_id": app_id, "app_secret": app_secret, "business_id": business_id}
                )
            ),
            encoding="utf-8",
        )
        rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "META")
        status = "CONECTADO" if app_id and app_secret else "DESCONECTADO"
        msg = "Meta Business Suite configurado." if status == "CONECTADO" else "Desconectado."
        if rows:
            return (
                self.mgr.update(
                    "INTEGR",
                    rows[0]["ID"],
                    {
                        "CLIENT_ID": app_id,
                        "CRED_REF": "documents/secrets/meta_graph.enc",
                        "SITUACAO": status,
                        "STATUS_MSG": msg,
                    },
                )
                or rows[0]
            )
        return self.mgr.insert(
            "INTEGR",
            {
                "PROVEDOR": "META",
                "SITUACAO": status,
                "CLIENT_ID": app_id,
                "CRED_REF": "documents/secrets/meta_graph.enc",
                "STATUS_MSG": msg,
                "TOTAL_SYNC": 0,
                "DT_ATUA": now_iso(),
            },
        )

    def load_config(self) -> Dict[str, Any]:
        sf = self.secrets_dir / "meta_graph.enc"
        if not sf.exists():
            return {}
        try:
            return json.loads(decrypt_secret_payload(sf.read_text(encoding="utf-8")))
        except Exception:
            return {}

