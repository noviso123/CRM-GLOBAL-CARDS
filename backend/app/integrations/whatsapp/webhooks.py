from typing import Any, Dict
from app.database.dbf_manager import DBFManager
from app.integrations.whatsapp.messages import WhatsAppService


def handle_whatsapp_webhook(mgr: DBFManager, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Processa webhook oficial da WhatsApp Business Platform (Meta Graph API)."""
    wa_svc = WhatsAppService(mgr)
    processed = 0
    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            val = change.get("value") or {}
            contacts = val.get("contacts") or []
            contact_name = (
                (contacts[0].get("profile") or {}).get("name", "") if contacts else ""
            )
            for msg in val.get("messages") or []:
                from_phone = msg.get("from", "")
                wamid = msg.get("id", "")
                text_body = (msg.get("text") or {}).get("body", "[Mídia recebida]")
                if from_phone:
                    conv = wa_svc.create_or_get_conversation(
                        telefone=from_phone, nome_cont=contact_name or from_phone
                    )
                    wa_svc.add_message(
                        conv_id=conv["ID"],
                        conteudo=text_body,
                        direcao="ENTRADA",
                        id_ext=wamid,
                    )
                    processed += 1
    return {"status": "PROCESSED", "messages_received": processed}

