import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import urllib.parse
import httpx
from app.core.config import settings
from app.core.exceptions import CRMSatiroException
from app.core.security import decrypt_secret_payload, encrypt_secret_payload
from app.database.dbf_manager import DBFManager
from app.utils.dates import now_iso


class BlingAuthManager:
    """Gerencia OAuth 2.0 oficial da API v3 do Bling com armazenamento criptografado local (nunca expõe tokens no frontend)."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.secrets_dir = self.mgr.documents_dir / "secrets"
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

    def _secret_file(self) -> Any:
        return self.secrets_dir / "bling_oauth.enc"

    def save_credentials(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8000/api/integrations/bling/oauth/callback",
        access_token: str = "",
        refresh_token: str = "",
        expires_in: int = 21600,
    ) -> Dict[str, Any]:
        existing = self.load_credentials()
        payload = {
            "client_id": client_id or existing.get("client_id", ""),
            "client_secret": client_secret or existing.get("client_secret", ""),
            "redirect_uri": redirect_uri or existing.get("redirect_uri", ""),
            "access_token": access_token or existing.get("access_token", ""),
            "refresh_token": refresh_token or existing.get("refresh_token", ""),
            "expires_at": (
                datetime.now() + timedelta(seconds=expires_in)
            ).strftime("%Y-%m-%dT%H:%M:%S")
            if access_token
            else existing.get("expires_at", ""),
        }
        cipher = encrypt_secret_payload(json.dumps(payload))
        with open(self._secret_file(), "w", encoding="utf-8") as f:
            f.write(cipher)

        rows = self.mgr.find_by_field("INTEGR", "PROVEDOR", "BLING")
        status = "CONECTADO" if payload.get("access_token") else "CONFIGURADO"
        msg = (
            "Autenticado via OAuth 2.0 Bling v3"
            if payload.get("access_token")
            else "Credenciais salvas. Aguardando autorização OAuth 2.0."
        )
        if rows:
            rec = self.mgr.update(
                "INTEGR",
                rows[0]["ID"],
                {
                    "CLIENT_ID": payload["client_id"],
                    "CRED_REF": "documents/secrets/bling_oauth.enc",
                    "SITUACAO": status,
                    "EXPIRA_EM": payload["expires_at"],
                    "STATUS_MSG": msg,
                },
            )
            return rec or rows[0]
        return self.mgr.insert(
            "INTEGR",
            {
                "PROVEDOR": "BLING",
                "SITUACAO": status,
                "CLIENT_ID": payload["client_id"],
                "CRED_REF": "documents/secrets/bling_oauth.enc",
                "EXPIRA_EM": payload["expires_at"],
                "STATUS_MSG": msg,
                "TOTAL_SYNC": 0,
                "DT_ATUA": now_iso(),
            },
        )

    def load_credentials(self) -> Dict[str, Any]:
        sf = self._secret_file()
        if not sf.exists():
            return {}
        try:
            raw = sf.read_text(encoding="utf-8")
            return json.loads(decrypt_secret_payload(raw))
        except Exception:
            return {}

    def get_authorize_url(self, state: str = "satiro_crm_bling") -> str:
        creds = self.load_credentials()
        client_id = creds.get("client_id", "")
        if not client_id:
            raise CRMSatiroException(
                "Configure o Client ID e Client Secret do Bling antes de iniciar o OAuth 2.0.",
                error_code="BLING_NOT_CONFIGURED",
            )
        params = urllib.parse.urlencode(
            {"response_type": "code", "client_id": client_id, "state": state}
        )
        return f"{settings.bling_oauth_authorize_url}?{params}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        creds = self.load_credentials()
        client_id = creds.get("client_id", "")
        client_secret = creds.get("client_secret", "")
        if not client_id or not client_secret:
            raise CRMSatiroException("Credenciais OAuth do Bling não configuradas.")

        basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                settings.bling_oauth_token_url,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                data={"grant_type": "authorization_code", "code": code},
            )
            if resp.status_code >= 400:
                raise CRMSatiroException(
                    f"Falha ao trocar código OAuth no Bling (HTTP {resp.status_code}).",
                    error_code="BLING_OAUTH_ERROR",
                )
            token_data = resp.json()
            return self.save_credentials(
                client_id=client_id,
                client_secret=client_secret,
                access_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", ""),
                expires_in=int(token_data.get("expires_in", 21600)),
            )

    def refresh_access_token(self) -> Optional[str]:
        creds = self.load_credentials()
        if not creds.get("refresh_token"):
            return None
        basic = base64.b64encode(
            f"{creds['client_id']}:{creds['client_secret']}".encode("utf-8")
        ).decode("ascii")
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                settings.bling_oauth_token_url,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": creds["refresh_token"],
                },
            )
            if resp.status_code >= 400:
                return None
            token_data = resp.json()
            self.save_credentials(
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
                access_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", creds["refresh_token"]),
                expires_in=int(token_data.get("expires_in", 21600)),
            )
            return token_data.get("access_token")

