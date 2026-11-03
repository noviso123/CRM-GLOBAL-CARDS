from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM
from app.database.dbf_manager import DBFManager
from app.integrations.whatsapp.client import WhatsAppCloudClient
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso
from app.utils.files import load_external_document, save_external_document
from app.utils.validators import normalize_digits


class WhatsAppService:
    """Gerencia conversas comerciais, vínculos com clientes/oportunidades e histórico de mensagens."""

    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.cloud = WhatsAppCloudClient(mgr)
        self.notif = NotificationService(mgr)

    def create_or_get_conversation(
        self,
        telefone: str,
        nome_cont: str,
        id_cliente: str = "",
        id_contato: str = "",
        id_oport: str = "",
        user_id: str = "SYSTEM",
    ) -> Dict[str, Any]:
        phone_norm = normalize_digits(telefone) or telefone.strip()
        existing = self.mgr.find_by_field("CONVERS", "TELEFONE", phone_norm)
        if existing:
            return self._enrich_conversation(existing[0])

        # Identifica automaticamente cliente existente pelo telefone/celular
        if not id_cliente and phone_norm:
            for cli in self.mgr.find_all("CLIENTES"):
                c_tel = normalize_digits(cli.get("TELEFONE", ""))
                c_cel = normalize_digits(cli.get("CELULAR", ""))
                if phone_norm.endswith(c_cel[-8:]) and len(c_cel) >= 8:
                    id_cliente = cli["ID"]
                    break
                if phone_norm.endswith(c_tel[-8:]) and len(c_tel) >= 8:
                    id_cliente = cli["ID"]
                    break

        rec = self.mgr.insert(
            "CONVERS",
            {
                "TELEFONE": phone_norm,
                "NOME_CONT": nome_cont.strip() or phone_norm,
                "ID_CLIENTE": id_cliente,
                "ID_CONTATO": id_contato,
                "ID_OPORT": id_oport,
                "SITUACAO": "EM_ATENDIMENTO",
                "NAO_LIDAS": 0,
                "ID_RESP": user_id,
            },
        )
        return self._enrich_conversation(rec)

    def _enrich_conversation(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(rec)
        if rec.get("ID_CLIENTE"):
            cli = self.mgr.get_by_id("CLIENTES", rec["ID_CLIENTE"])
            item["CLIENTE_NOME"] = cli["NOME"] if cli else ""
        else:
            item["CLIENTE_NOME"] = ""
        if rec.get("ID_OPORT"):
            opp = self.mgr.get_by_id("OPORTUN", rec["ID_OPORT"])
            item["OPORTUNIDADE_TITULO"] = opp["TITULO"] if opp else ""
        else:
            item["OPORTUNIDADE_TITULO"] = ""
        return item

    def list_conversations(
        self, situacao: Optional[str] = None, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()
        rows = self.mgr.find_all("CONVERS", sort_by="DT_ATUA", descending=True)
        out: List[Dict[str, Any]] = []
        for r in rows:
            enr = self._enrich_conversation(r)
            if situacao and enr.get("SITUACAO") != situacao.upper():
                continue
            if q and q not in f"{enr.get('NOME_CONT','')} {enr.get('TELEFONE','')} {enr.get('CLIENTE_NOME','')}".upper():
                continue
            out.append(enr)
        return out

    def link_conversation(
        self,
        conv_id: str,
        id_cliente: Optional[str] = None,
        id_contato: Optional[str] = None,
        id_oport: Optional[str] = None,
        situacao: Optional[str] = None,
        obs_atend: Optional[str] = None,
        user_id: str = "SYSTEM",
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("CONVERS", conv_id)
        if not curr:
            raise NotFoundErrorCRM("CONVERS", conv_id)
        changes: Dict[str, Any] = {}
        if id_cliente is not None:
            changes["ID_CLIENTE"] = id_cliente
        if id_contato is not None:
            changes["ID_CONTATO"] = id_contato
        if id_oport is not None:
            changes["ID_OPORT"] = id_oport
        if situacao is not None:
            changes["SITUACAO"] = situacao
        if obs_atend is not None:
            changes["OBS_ATEND"] = obs_atend

        updated = self.mgr.update("CONVERS", conv_id, changes) or curr
        if updated.get("ID_CLIENTE"):
            self.notif.record_history(
                "WHATSAPP",
                conv_id,
                "VINCULO_COMERCIAL",
                f"Conversa WhatsApp ({updated['TELEFONE']}) associada ao cliente.",
                id_cliente=updated["ID_CLIENTE"],
                id_usuario=user_id,
            )
        return self._enrich_conversation(updated)

    def add_message(
        self,
        conv_id: str,
        conteudo: str,
        direcao: str = "SAIDA",
        tipo_msg: str = "TEXTO",
        user_id: str = "SYSTEM",
        id_ext: str = "",
    ) -> Dict[str, Any]:
        conv = self.mgr.get_by_id("CONVERS", conv_id)
        if not conv:
            raise NotFoundErrorCRM("CONVERS", conv_id)

        status_ent = "RECEBIDA" if direcao.upper() == "ENTRADA" else "ENVIADA"
        wamid = id_ext
        if direcao.upper() == "SAIDA" and tipo_msg.upper() != "NOTA_INTERNA":
            dispatch = self.cloud.send_cloud_text_message(conv["TELEFONE"], conteudo)
            if dispatch.get("dispatched_external"):
                status_ent = "ENTREGUE"
                wamid = dispatch.get("wamid", "")

        msg_rec = self.mgr.insert(
            "MENSAGEN",
            {
                "ID_CONVERS": conv_id,
                "DIRECAO": direcao.upper(),
                "TIPO_MSG": tipo_msg.upper(),
                "CONTEUDO": conteudo[:250],
                "STATUS_ENT": status_ent,
                "ID_USUARIO": user_id,
                "ID_EXT": wamid,
                "DT_ENVIO": now_iso(),
            },
        )
        if len(conteudo) > 250:
            doc_ref = save_external_document(
                self.mgr.base_dir,
                "whatsapp_messages",
                msg_rec["ID"],
                {"full_content": conteudo},
            )
            msg_rec = self.mgr.update("MENSAGEN", msg_rec["ID"], {"DOC_REF": doc_ref}) or msg_rec

        unread = int(conv.get("NAO_LIDAS", 0)) + (1 if direcao.upper() == "ENTRADA" else 0)
        if direcao.upper() == "SAIDA":
            unread = 0
        self.mgr.update(
            "CONVERS",
            conv_id,
            {
                "ULT_MSG": conteudo[:160],
                "DT_ULT_MSG": msg_rec["DT_ENVIO"],
                "NAO_LIDAS": unread,
            },
        )
        if conv.get("ID_CLIENTE"):
            self.mgr.update("CLIENTES", conv["ID_CLIENTE"], {"DT_ULT_INT": now_iso()})
        if direcao.upper() == "ENTRADA":
            self.notif.notify(
                "NOVA_MENSAGEM",
                f"Nova mensagem de {conv['NOME_CONT']}",
                conteudo[:180],
                entidade="WHATSAPP",
                id_ref=conv_id,
            )
        return msg_rec

    def list_messages(self, conv_id: str) -> List[Dict[str, Any]]:
        if not self.mgr.get_by_id("CONVERS", conv_id):
            raise NotFoundErrorCRM("CONVERS", conv_id)
        self.mgr.update("CONVERS", conv_id, {"NAO_LIDAS": 0})
        msgs = self.mgr.find_by_field("MENSAGEN", "ID_CONVERS", conv_id)
        msgs.sort(key=lambda m: m.get("DT_ENVIO", ""))
        out: List[Dict[str, Any]] = []
        for m in msgs:
            item = dict(m)
            if m.get("DOC_REF"):
                ext = load_external_document(self.mgr.base_dir, m["DOC_REF"])
                if ext.get("full_content"):
                    item["CONTEUDO"] = ext["full_content"]
            out.append(item)
        return out

    def list_templates(self) -> List[Dict[str, Any]]:
        """Retorna lista de templates HSM oficiais pré-aprovados para uso comercial."""
        return [
            {
                "id": "confirmacao_pedido",
                "name": "confirmacao_pedido",
                "label": "Confirmação de Pedido",
                "category": "UTILITY",
                "description": "Notifica o cliente sobre a confirmação e aprovação do pedido de venda.",
                "example": "Olá {{1}}, confirmamos o seu pedido {{2}} no valor de R$ {{3}} na Global Cards!",
                "parameters": ["Nome do Cliente", "Número do Pedido", "Valor Total"],
            },
            {
                "id": "pedido_faturado",
                "name": "pedido_faturado",
                "label": "Pedido Faturado & Expedição",
                "category": "UTILITY",
                "description": "Informa emissão da nota fiscal e envio para produção/transporte.",
                "example": "Olá {{1}}, seu pedido {{2}} foi faturado! A nota fiscal foi emitida e os produtos estão em rota.",
                "parameters": ["Nome do Cliente", "Número do Pedido"],
            },
            {
                "id": "orcamento_gerado",
                "name": "orcamento_gerado",
                "label": "Proposta Comercial / Orçamento",
                "category": "MARKETING",
                "description": "Envia aviso de orçamento gerado com condições exclusivas.",
                "example": "Olá {{1}}, preparamos sua cotação nº {{2}} na Global Cards! Confira os preços especiais.",
                "parameters": ["Nome do Cliente", "Número do Orçamento"],
            },
            {
                "id": "cobranca_pix",
                "name": "cobranca_pix",
                "label": "Cobrança com Chave PIX",
                "category": "UTILITY",
                "description": "Envia chave PIX e valor para liquidação rápida do pedido.",
                "example": "Olá {{1}}, segue os dados para pagamento via PIX do seu pedido {{2}} no valor de R$ {{3}}.",
                "parameters": ["Nome do Cliente", "Número do Pedido", "Valor"],
            },
            {
                "id": "boas_vindas",
                "name": "boas_vindas",
                "label": "Boas-vindas ao Cliente",
                "category": "MARKETING",
                "description": "Primeiro contato comercial amigável da Global Cards.",
                "example": "Olá {{1}}, seja bem-vindo à Global Cards! Como podemos ajudar com seus crachás e cordões hoje?",
                "parameters": ["Nome do Cliente"],
            },
        ]

    def send_template(
        self,
        conv_id: str,
        template_name: str,
        parameters: Optional[List[str]] = None,
        user_id: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """Dispara template oficial via Meta Cloud API e registra no histórico da conversa."""
        conv = self.mgr.get_by_id("CONVERS", conv_id)
        if not conv:
            raise NotFoundErrorCRM("CONVERS", conv_id)

        params = parameters or []
        dispatch = self.cloud.send_cloud_template_message(
            to_phone=conv["TELEFONE"],
            template_name=template_name,
            parameters=params,
        )

        preview_text = f"[TEMPLATE: {template_name}] " + " | ".join(str(p) for p in params)
        msg_rec = self.mgr.insert(
            "MENSAGEN",
            {
                "ID_CONVERS": conv_id,
                "DIRECAO": "SAIDA",
                "TIPO_MSG": "TEMPLATE",
                "CONTEUDO": preview_text[:250],
                "STATUS_ENT": "ENTREGUE" if dispatch.get("dispatched_external") else "PENDENTE",
                "ID_USUARIO": user_id,
                "ID_EXT": dispatch.get("wamid", ""),
                "DT_ENVIO": now_iso(),
            },
        )

        self.mgr.update(
            "CONVERS",
            conv_id,
            {
                "ULT_MSG": preview_text[:160],
                "DT_ULT_MSG": msg_rec["DT_ENVIO"],
                "NAO_LIDAS": 0,
            },
        )

        if conv.get("ID_CLIENTE"):
            self.mgr.update("CLIENTES", conv["ID_CLIENTE"], {"DT_ULT_INT": now_iso()})

        return {
            "message": msg_rec,
            "dispatch": dispatch,
            "template": template_name,
        }

