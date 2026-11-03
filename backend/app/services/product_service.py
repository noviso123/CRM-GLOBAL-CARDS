from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.integrity import IntegrityValidator
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate
from app.services.notification_service import NotificationService
from app.utils.dates import now_iso
from app.utils.files import load_external_document, save_external_document


class ProductService:
    def __init__(self, mgr: DBFManager):
        self.mgr = mgr
        self.integrity = IntegrityValidator(mgr)
        self.notif = NotificationService(mgr)

    def create_category(self, data: CategoryCreate) -> Dict[str, Any]:
        payload = data.model_dump()
        if not payload.get("CODIGO"):
            payload["CODIGO"] = self.mgr.next_sequence_code("CATEGORIAS", "CAT")
        return self.mgr.insert("CATEGORIAS", payload)

    def list_categories(self) -> List[Dict[str, Any]]:
        return self.mgr.find_all("CATEGORIAS", sort_by="ORDEM")

    def create_product(self, data: ProductCreate, user_id: str = "SYSTEM") -> Dict[str, Any]:
        codigo = data.CODIGO or self.mgr.next_sequence_code("PRODUTOS", "PRD")
        payload = data.model_dump(
            exclude={"DESCRICAO_COMPLETA", "GALERIA_IMAGENS", "ESPECIFICACOES"}
        )
        payload["CODIGO"] = codigo
        payload["ID_RESP"] = user_id
        rec = self.mgr.insert("PRODUTOS", payload)

        if data.DESCRICAO_COMPLETA or data.GALERIA_IMAGENS or data.ESPECIFICACOES:
            doc_ref = save_external_document(
                self.mgr.base_dir,
                "products",
                rec["ID"],
                {
                    "full_description": data.DESCRICAO_COMPLETA or data.DESC_CURTA or "",
                    "gallery": data.GALERIA_IMAGENS or ([data.IMG_PRINC] if data.IMG_PRINC else []),
                    "specifications": data.ESPECIFICACOES or {},
                    "updated_at": now_iso(),
                },
            )
            rec = self.mgr.update("PRODUTOS", rec["ID"], {"DOC_REF": doc_ref}) or rec

        self.notif.record_history(
            "PRODUTO",
            rec["ID"],
            "CRIACAO",
            f"Produto {rec['NOME']} ({rec['CODIGO']}) cadastrado a R$ {rec['PRECO']:.2f}.",
            id_usuario=user_id,
        )
        return self._enrich_product(rec)

    def _enrich_product(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(rec)
        if item.get("ID_CATEG"):
            cat = self.mgr.get_by_id("CATEGORIAS", item["ID_CATEG"])
            item["CATEGORIA_NOME"] = cat["NOME"] if cat else ""
        else:
            item["CATEGORIA_NOME"] = "Geral"
        ext = load_external_document(self.mgr.base_dir, item.get("DOC_REF"))
        item["DETAILS"] = ext
        return item

    def get_product(self, product_id: str) -> Dict[str, Any]:
        rec = self.mgr.get_by_id("PRODUTOS", product_id)
        if not rec:
            raise NotFoundErrorCRM("PRODUTOS", product_id)
        return self._enrich_product(rec)

    def update_product(
        self, product_id: str, data: ProductUpdate, user_id: str = "SYSTEM"
    ) -> Dict[str, Any]:
        curr = self.mgr.get_by_id("PRODUTOS", product_id)
        if not curr:
            raise NotFoundErrorCRM("PRODUTOS", product_id)
        changes = data.model_dump(
            exclude_unset=True,
            exclude={"DESCRICAO_COMPLETA", "GALERIA_IMAGENS", "ESPECIFICACOES"},
        )
        if (
            data.DESCRICAO_COMPLETA is not None
            or data.GALERIA_IMAGENS is not None
            or data.ESPECIFICACOES is not None
        ):
            old_ext = load_external_document(self.mgr.base_dir, curr.get("DOC_REF"))
            doc_ref = save_external_document(
                self.mgr.base_dir,
                "products",
                product_id,
                {
                    "full_description": data.DESCRICAO_COMPLETA
                    if data.DESCRICAO_COMPLETA is not None
                    else old_ext.get("full_description", ""),
                    "gallery": data.GALERIA_IMAGENS
                    if data.GALERIA_IMAGENS is not None
                    else old_ext.get("gallery", []),
                    "specifications": data.ESPECIFICACOES
                    if data.ESPECIFICACOES is not None
                    else old_ext.get("specifications", {}),
                    "updated_at": now_iso(),
                },
            )
            changes["DOC_REF"] = doc_ref

        updated = self.mgr.update("PRODUTOS", product_id, changes) or curr
        self.notif.record_history(
            "PRODUTO",
            product_id,
            "ATUALIZACAO",
            f"Produto {updated['NOME']} atualizado.",
            id_usuario=user_id,
        )
        return self._enrich_product(updated)

    def delete_product(self, product_id: str) -> bool:
        self.integrity.check_product_can_be_deleted(product_id)
        return self.mgr.delete("PRODUTOS", product_id)

    def list_products(
        self,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        situacao: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        q = (search or "").strip().upper()

        def _pred(r: Dict[str, Any]) -> bool:
            if category_id and r.get("ID_CATEG") != category_id:
                return False
            if situacao and r.get("SITUACAO") != situacao.upper():
                return False
            price = float(r.get("PRECO", 0.0))
            if min_price is not None and price < min_price:
                return False
            if max_price is not None and price > max_price:
                return False
            if q:
                haystack = f"{r.get('CODIGO','')} {r.get('NOME','')} {r.get('DESC_CURTA','')}".upper()
                if q not in haystack:
                    return False
            return True

        rows = self.mgr.find_all("PRODUTOS", predicate=_pred, sort_by="NOME")
        return [self._enrich_product(r) for r in rows]

