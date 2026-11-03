from typing import List, Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    CODIGO: Optional[str] = None
    NOME: str = Field(..., min_length=2, max_length=80)
    ID_PAI: Optional[str] = ""
    ORDEM: int = 1
    ICONE: Optional[str] = "Package"
    SITUACAO: str = "ATIVO"


class ProductCreate(BaseModel):
    CODIGO: Optional[str] = None
    NOME: str = Field(..., min_length=2, max_length=120)
    DESC_CURTA: Optional[str] = ""
    DESCRICAO_COMPLETA: Optional[str] = ""
    GALERIA_IMAGENS: Optional[List[str]] = None
    ESPECIFICACOES: Optional[dict] = None
    ID_CATEG: Optional[str] = ""
    UNIDADE: str = "UN"
    PRECO: float = Field(default=0.0, ge=0.0)
    PRECO_CUST: float = Field(default=0.0, ge=0.0)
    DESC_MAX: float = Field(default=10.0, ge=0.0, le=100.0)
    ESTOQUE: float = 0.0
    EST_MIN: float = 0.0
    IMG_PRINC: Optional[str] = ""
    DESTAQUE: bool = False
    SITUACAO: str = "ATIVO"
    ORIGEM: str = "LOCAL"
    ID_EXT: Optional[str] = ""


class ProductUpdate(BaseModel):
    CODIGO: Optional[str] = None
    NOME: Optional[str] = None
    DESC_CURTA: Optional[str] = None
    DESCRICAO_COMPLETA: Optional[str] = None
    GALERIA_IMAGENS: Optional[List[str]] = None
    ESPECIFICACOES: Optional[dict] = None
    ID_CATEG: Optional[str] = None
    UNIDADE: Optional[str] = None
    PRECO: Optional[float] = None
    PRECO_CUST: Optional[float] = None
    DESC_MAX: Optional[float] = None
    ESTOQUE: Optional[float] = None
    EST_MIN: Optional[float] = None
    IMG_PRINC: Optional[str] = None
    DESTAQUE: Optional[bool] = None
    SITUACAO: Optional[str] = None

