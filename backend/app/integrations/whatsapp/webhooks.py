from typing import Any, Dict
from app.database.dbf_manager import DBFManager
from app.integrations.whatsapp.messages import WhatsAppService


def handle_whatsapp_webhook(mgr: DBFManager, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Processa webhook oficial da WhatsApp Business Platform (Meta Graph API v21.0)."""
    wa_svc = WhatsAppService(mgr)
    processed_messages = 0
    processed_statuses = 0

    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            val = change.get("value") or {}
            contacts = val.get("contacts") or []
            contact_name = (
                (contacts[0].get("profile") or {}).get("name", "") if contacts else ""
            )

            # 1. Processa mensagens recebidas do cliente
            for msg in val.get("messages") or []:
                from_phone = msg.get("from", "")
                wamid = msg.get("id", "")
                msg_type = msg.get("type", "text")

                text_body = ""
                if msg_type == "text":
                    text_body = (msg.get("text") or {}).get("body", "")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive") or {}
                    btn_reply = interactive.get("button_reply") or {}
                    list_reply = interactive.get("list_reply") or {}
                    text_body = btn_reply.get("title") or list_reply.get("title") or "[Opção selecionada]"
                elif msg_type == "button":
                    text_body = (msg.get("button") or {}).get("text", "[Botão]")
                elif msg_type in ("image", "document", "audio", "video"):
                    caption = (msg.get(msg_type) or {}).get("caption", "")
                    text_body = f"[{msg_type.upper()}] {caption}".strip()
                else:
                    text_body = f"[{msg_type.upper()}]"

                if from_phone and text_body:
                    conv = wa_svc.create_or_get_conversation(
                        telefone=from_phone, nome_cont=contact_name or from_phone
                    )
                    wa_svc.add_message(
                        conv_id=conv["ID"],
                        conteudo=text_body,
                        direcao="ENTRADA",
                        tipo_msg="TEXTO" if msg_type == "text" else "INTERATIVO",
                        id_ext=wamid,
                    )
                    processed_messages += 1

            # 2. Processa status de entrega da Meta (sent, delivered, read, failed)
            for st in val.get("statuses") or []:
                wamid = st.get("id", "")
                raw_status = (st.get("status") or "").lower()
                status_map = {
                    "sent": "ENVIADA",
                    "delivered": "ENTREGUE",
                    "read": "LIDA",
                    "failed": "FALHA",
                }
                new_status = status_map.get(raw_status)
                if wamid and new_status:
                    msgs = mgr.find_by_field("MENSAGEN", "ID_EXT", wamid)
                    if msgs:
                        mgr.update("MENSAGEN", msgs[0]["ID"], {"STATUS_ENT": new_status})
                        processed_statuses += 1

    return {
        "status": "PROCESSED",
        "messages_received": processed_messages,
        "statuses_updated": processed_statuses,
    }
