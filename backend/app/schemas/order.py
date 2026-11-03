from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemInput(BaseModel):
    ID_PRODUTO: str
    QUANTIDADE: float = Field(..., gt=0)
    PRECO_UNIT: Optional[float] = None
    DESC_VALOR: float = Field(default=0.0, ge=0.0)


class OrderCreate(BaseModel):
    ID_CLIENTE: str
    ID_ORCAM: Optional[str] = ""
    ID_OPORT: Optional[str] = ""
    DT_PEDIDO: Optional[str] = None
    FRETE: float = Field(default=0.0, ge=0.0)
    DESCONTO_EXTRA: float = Field(default=0.0, ge=0.0)
    COND_PAGTO: Optional[str] = "À Vista"
    OBS: Optional[str] = ""
    SITUACAO: str = "ABERTO"
    ORIGEM: str = "LOCAL"
    ITEMS: List[OrderItemInput] = Field(..., min_length=1)

