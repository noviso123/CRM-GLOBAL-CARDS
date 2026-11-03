from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user, get_dbf_manager
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.integrations.suppliers.service import SupplierService

router = APIRouter(prefix="/api/suppliers", tags=["Fornecedores Gráficos"])


class ExtractUrlRequest(BaseModel):
    url: str = Field(..., min_length=5, description="URL do produto no fornecedor")


class ImportProductRequest(BaseModel):
    fornecedor_id: str
    fornecedor_nome: str
    nome: str
    sku: Optional[str] = None
    categoria: Optional[str] = None
    categoria_id: Optional[str] = None
    modo_venda: str = "UN"  # "UN" ou "LOTE"
    lote_quantidade: int = 1
    preco_custo: float = 0.0
    preco_venda: float = 0.0
    estoque_inicial: float = 0.0
    estoque_minimo: float = 10.0
    imagem: Optional[str] = ""
    galeria: Optional[List[str]] = None
    descricao: Optional[str] = ""
    especificacoes: Optional[Dict[str, Any]] = None
    url_origem: Optional[str] = ""


@router.get("/partners")
def list_partners(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    """Lista os 4 fornecedores gráficos parceiros homologados."""
    check_permission(mgr, user, "PRODUTOS", "view")
    return SupplierService(mgr).list_suppliers()


@router.get("/catalog")
def search_catalog(
    q: Optional[str] = Query(None, description="Busca por termo ou palavra-chave"),
    supplier: Optional[str] = Query(None, description="ID do fornecedor ou 'ALL'"),
    category: Optional[str] = Query(None, description="Categoria do produto"),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    """Consulta catálogo unificado de produtos disponíveis para importação com 1 clique."""
    check_permission(mgr, user, "PRODUTOS", "view")
    return SupplierService(mgr).search_catalog(query=q, supplier_id=supplier, category=category)


@router.post("/extract-url")
def extract_from_url(
    payload: ExtractUrlRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Extrai fotos, especificações, preços e tiragens a partir da URL de um dos fornecedores."""
    check_permission(mgr, user, "PRODUTOS", "create")
    return SupplierService(mgr).extract_from_url(payload.url)


@router.post("/import", status_code=status.HTTP_201_CREATED)
def import_supplier_product(
    payload: ImportProductRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    """Importa produto diretamente para PRODUTOS.DBF do CRM e sincroniza automaticamente com o Bling."""
    check_permission(mgr, user, "PRODUTOS", "create")
    return SupplierService(mgr).import_product(payload.model_dump(), user_id=user["ID"])

