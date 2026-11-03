from typing import Any, Dict
from app.database.dbf_manager import DBFManager
from app.integrations.bling.sync import BlingSyncService


def handle_bling_webhook(mgr: DBFManager, payload: Dict[str, Any]) -> Dict[str, Any]:
    sync_svc = BlingSyncService(mgr)
    event_type = str(payload.get("event", payload.get("tipo", ""))).lower()
    data = payload.get("data", payload)
    if "produto" in event_type or "product" in event_type:
        return sync_svc.upsert_bling_product(data)
    if "contato" in event_type or "contact" in event_type:
        return sync_svc.upsert_bling_client(data)
    if "pedido" in event_type or "order" in event_type:
        return sync_svc.upsert_bling_order(data)
    return {"action": "IGNORED", "reason": "Evento não mapeado"}

