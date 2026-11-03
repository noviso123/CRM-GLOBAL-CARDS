from typing import Optional
from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    TITULO: str = Field(..., min_length=2, max_length=100)
    ID_CLIENTE: str
    ID_CONTATO: Optional[str] = ""
    ID_FUNIL: Optional[str] = ""
    ID_ETAPA: Optional[str] = ""
    VALOR_EST: float = Field(default=0.0, ge=0.0)
    PROBABIL: Optional[float] = None
    DT_PREV: Optional[str] = ""
    PROX_ATIV: Optional[str] = ""
    OBS: Optional[str] = ""
    ORIGEM: str = "PROSPECCAO"
    ID_RESP: Optional[str] = ""


class OpportunityUpdate(BaseModel):
    TITULO: Optional[str] = None
    ID_CLIENTE: Optional[str] = None
    ID_CONTATO: Optional[str] = None
    ID_ETAPA: Optional[str] = None
    VALOR_EST: Optional[float] = None
    PROBABIL: Optional[float] = None
    DT_PREV: Optional[str] = None
    PROX_ATIV: Optional[str] = None
    MOT_PERDA: Optional[str] = None
    OBS: Optional[str] = None
    ORIGEM: Optional[str] = None
    SITUACAO: Optional[str] = None
    ID_RESP: Optional[str] = None


class StageCreate(BaseModel):
    ID_FUNIL: str
    NOME: str
    ORDEM: int = 1
    COR: str = "#0284C7"
    PROB_PAD: float = 50.0
    TIPO_ETAPA: str = "ABERTA"

