from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_current_user, get_dbf_manager, paginate_items
from app.core.permissions import check_permission
from app.database.dbf_manager import DBFManager
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["Produtos"])


@router.get("/categories")
def list_categories(
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> List[Dict[str, Any]]:
    check_permission(mgr, user, "PRODUTOS", "view")
    return ProductService(mgr).list_categories()


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "create")
    return ProductService(mgr).create_category(payload)


@router.get("")
def list_products(
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    situacao: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "view")
    rows = ProductService(mgr).list_products(
        search=search,
        category_id=category_id,
        situacao=situacao,
        min_price=min_price,
        max_price=max_price,
    )
    return paginate_items(rows, page=page, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "create")
    return ProductService(mgr).create_product(payload, user_id=user["ID"])


@router.get("/{product_id}")
def get_product(
    product_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "view")
    return ProductService(mgr).get_product(product_id)


@router.put("/{product_id}")
def update_product(
    product_id: str,
    payload: ProductUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "edit")
    return ProductService(mgr).update_product(product_id, payload, user_id=user["ID"])


@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    check_permission(mgr, user, "PRODUTOS", "delete")
    ProductService(mgr).delete_product(product_id)
    return {"deleted": True, "id": product_id}

