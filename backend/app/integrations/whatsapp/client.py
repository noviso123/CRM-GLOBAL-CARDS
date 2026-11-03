import json
from typing import Any, Dict
import httpx
from app.core.config import settings
from app.core.security import decrypt_secret_payload, encrypt_secret_payload
from app.database.dbf_manager import DBFManager
from app.utils.dates import now_iso


class WhatsAppCloudClient:
    """Cliente oficial WhatsApp Business Platform / Cloud API (sem scraping ou automação de DOM)."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.secrets_dir = self.mgr.documents_dir / "secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

    def _secret_file(self) -> Any:
        return self.secrets_dir / "whatsapp_cloud.enc"

    def save_config(
        self, phone_number_id: str, access_token: str, verify_token: str = "satiro_wa_verify"
    ) -> Dict[str, Any]:
        payload = {
            "phone_number_id": phone_number_id.strip(),
            "access_token": access_token.strip(),
            "verify_token": verify_token.strip(),
        }
        self._secret_file().write_text(
            encrypt_secret_payload(json.dumps(payload)), encoding="utf-8"
        )
        rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "WHATSAPP")
        status = "CONECTADO" if phone_number_id and access_token else "DESCONECTADO"
        msg = "WhatsApp Business Cloud API configurado." if status == "CONECTADO" else "Credenciais incompletas."
        if rows:
            return (
                self.mgr.update(
                    "INTEGR",
                    rows[0]["ID"],
                    {
                        "CLIENT_ID": phone_number_id,
                        "CRED_REF": "documents/secrets/whatsapp_cloud.enc",
                        "SITUACAO": status,
                        "STATUS_MSG": msg,
                    },
                )
                or rows[0]
            )
        return self.mgr.insert(
            "INTEGR",
            {
                "PROVEDOR": "WHATSAPP",
                "SITUACAO": status,
                "CLIENT_ID": phone_number_id,
                "CRED_REF": "documents/secrets/whatsapp_cloud.enc",
                "STATUS_MSG": msg,
                "TOTAL_SYNC": 0,
                "DT_ATUA": now_iso(),
            },
        )

    def load_config(self) -> Dict[str, Any]:
        sf = self._secret_file()
        if not sf.exists():
            return {}
        try:
            return json.loads(decrypt_secret_payload(sf.read_text(encoding="utf-8")))
        except Exception:
            return {}

    def send_cloud_text_message(self, to_phone: str, text_body: str) -> Dict[str, Any]:
        cfg = self.load_config()
        phone_id = cfg.get("phone_number_id")
        token = cfg.get("access_token")
        if not phone_id or not token:
            return {"dispatched_external": False, "reason": "WHATSAPP_CLOUD_NOT_CONFIGURED"}

        url = f"{settings.whatsapp_graph_url}/{phone_id}/messages"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to_phone,
                    "type": "text",
                    "text": {"body": text_body},
                },
            )
            if resp.status_code >= 400:
                return {"dispatched_external": False, "http_status": resp.status_code}
            data = resp.json()
            wamid = (data.get("messages") or [{}])[0].get("id", "")
            return {"dispatched_external": True, "wamid": wamid}

