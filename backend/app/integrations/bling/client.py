from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import CRMSatiroException
from app.database.dbf_manager import DBFManager
from app.integrations.bling.auth import BlingAuthManager


class BlingAPIClient:
    """Cliente HTTP para a API v3 do Bling com renovação automática de token e tratamento de limites."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.auth = BlingAuthManager(mgr)

    def _get_token(self) -> str:
        creds = self.auth.load_credentials()
        token = creds.get("access_token", "")
        if not token:
            raise CRMSatiroException(
                "Integração Bling não possui Access Token ativo. Realize a autorização OAuth 2.0 nas Configurações.",
                error_code="BLING_TOKEN_MISSING",
            )
        return token

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        token = self._get_token()
        url = f"{settings.bling_api_base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=25.0) as client:
            resp = client.get(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                params=params or {},
            )
            if resp.status_code == 401:
                new_token = self.auth.refresh_access_token()
                if new_token:
                    resp = client.get(
                        url,
                        headers={"Authorization": f"Bearer {new_token}", "Accept": "application/json"},
                        params=params or {},
                    )
            if resp.status_code >= 400:
                raise CRMSatiroException(
                    f"Erro na requisição ao Bling ({endpoint}): HTTP {resp.status_code}",
                    error_code="BLING_API_ERROR",
                )
            return resp.json()

    def post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        token = self._get_token()
        url = f"{settings.bling_api_base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=json_data,
            )
            if resp.status_code == 401:
                new_token = self.auth.refresh_access_token()
                if new_token:
                    resp = client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {new_token}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json=json_data,
                    )
            if resp.status_code >= 400:
                raise CRMSatiroException(
                    f"Erro no envio de dados ao Bling ({endpoint}): HTTP {resp.status_code} - {resp.text}",
                    error_code="BLING_API_ERROR",
                )
            return resp.json()

    def patch(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        token = self._get_token()
        url = f"{settings.bling_api_base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=25.0) as client:
            resp = client.patch(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=json_data,
            )
            if resp.status_code == 401:
                new_token = self.auth.refresh_access_token()
                if new_token:
                    resp = client.patch(
                        url,
                        headers={
                            "Authorization": f"Bearer {new_token}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json=json_data,
                    )
            if resp.status_code >= 400:
                raise CRMSatiroException(
                    f"Erro na atualização de dados no Bling ({endpoint}): HTTP {resp.status_code} - {resp.text}",
                    error_code="BLING_API_ERROR",
                )
            return resp.json()


