from typing import Optional
from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    ID_CLIENTE: str
    NOME: str = Field(..., min_length=2, max_length=80)
    CARGO: Optional[str] = ""
    DEPTO: Optional[str] = ""
    TELEFONE: Optional[str] = ""
    CELULAR: Optional[str] = ""
    EMAIL: Optional[str] = ""
    PRINCIPAL: bool = False
    OBS: Optional[str] = ""
    SITUACAO: str = "ATIVO"
    ORIGEM: str = "LOCAL"
    ID_RESP: Optional[str] = ""


class ContactUpdate(BaseModel):
    ID_CLIENTE: Optional[str] = None
    NOME: Optional[str] = None
    CARGO: Optional[str] = None
    DEPTO: Optional[str] = None
    TELEFONE: Optional[str] = None
    CELULAR: Optional[str] = None
    EMAIL: Optional[str] = None
    PRINCIPAL: Optional[bool] = None
    OBS: Optional[str] = None
    SITUACAO: Optional[str] = None

