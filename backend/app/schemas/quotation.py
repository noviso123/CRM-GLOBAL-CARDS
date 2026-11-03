from typing import List, Optional
from pydantic import BaseModel, Field


class QuotationItemInput(BaseModel):
    ID_PRODUTO: str
    QUANTIDADE: float = Field(..., gt=0)
    PRECO_UNIT: Optional[float] = None
    DESC_VALOR: float = Field(default=0.0, ge=0.0)
    OBS_ITEM: Optional[str] = ""


class QuotationCreate(BaseModel):
    ID_CLIENTE: str
    ID_CONTATO: Optional[str] = ""
    ID_OPORT: Optional[str] = ""
    DT_EMISSAO: Optional[str] = None
    DT_VALID: Optional[str] = None
    FRETE: float = Field(default=0.0, ge=0.0)
    DESCONTO_EXTRA: float = Field(default=0.0, ge=0.0)
    OBS: Optional[str] = ""
    SITUACAO: str = "EM_ELABORACAO"
    ITEMS: List[QuotationItemInput] = Field(..., min_length=1)

