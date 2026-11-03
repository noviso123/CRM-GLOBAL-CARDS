from typing import Any, Dict, List
from app.integrations.bling.client import BlingAPIClient


def fetch_bling_products(api: BlingAPIClient, pagina: int = 1, limite: int = 100) -> List[Dict[str, Any]]:
    res = api.get("produtos", params={"pagina": pagina, "limite": limite})
    return res.get("data", [])

