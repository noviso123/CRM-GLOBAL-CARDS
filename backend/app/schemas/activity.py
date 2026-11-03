from typing import Optional
from pydantic import BaseModel, Field


class ActivityCreate(BaseModel):
    TITULO: str = Field(..., min_length=2, max_length=100)
    DESCRICAO: Optional[str] = ""
    TIPO: str = "TAREFA"
    ID_CLIENTE: Optional[str] = ""
    ID_OPORT: Optional[str] = ""
    DATA_AG: str
    HORA_AG: Optional[str] = "09:00"
    DT_PRAZO: Optional[str] = ""
    PRIORIDADE: str = "MEDIA"
    SITUACAO: str = "PENDENTE"
    ID_RESP: Optional[str] = ""


class ActivityUpdate(BaseModel):
    TITULO: Optional[str] = None
    DESCRICAO: Optional[str] = None
    TIPO: Optional[str] = None
    ID_CLIENTE: Optional[str] = None
    ID_OPORT: Optional[str] = None
    DATA_AG: Optional[str] = None
    HORA_AG: Optional[str] = None
    DT_PRAZO: Optional[str] = None
    PRIORIDADE: Optional[str] = None
    SITUACAO: Optional[str] = None
    ID_RESP: Optional[str] = None

