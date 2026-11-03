from typing import Optional
from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    CODIGO: Optional[str] = None
    TIPO_PES: str = Field(default="PJ", pattern="^(PF|PJ)$")
    NOME: str = Field(..., min_length=2, max_length=100)
    FANTASIA: Optional[str] = ""
    CPF_CNPJ: Optional[str] = ""
    INSC_EST: Optional[str] = ""
    EMAIL: Optional[str] = ""
    TELEFONE: Optional[str] = ""
    CELULAR: Optional[str] = ""
    ENDERECO: Optional[str] = ""
    NUMERO: Optional[str] = ""
    COMPLEM: Optional[str] = ""
    BAIRRO: Optional[str] = ""
    CIDADE: Optional[str] = ""
    UF: Optional[str] = ""
    CEP: Optional[str] = ""
    PAIS: str = "Brasil"
    OBS_CURTA: Optional[str] = ""
    OBSERVACOES_LONGAS: Optional[str] = ""
    SITUACAO: str = "ATIVO"
    ORIGEM: str = "LOCAL"
    ID_EXT: Optional[str] = ""
    ID_RESP: Optional[str] = ""


class ClientUpdate(BaseModel):
    TIPO_PES: Optional[str] = None
    NOME: Optional[str] = None
    FANTASIA: Optional[str] = None
    CPF_CNPJ: Optional[str] = None
    INSC_EST: Optional[str] = None
    EMAIL: Optional[str] = None
    TELEFONE: Optional[str] = None
    CELULAR: Optional[str] = None
    ENDERECO: Optional[str] = None
    NUMERO: Optional[str] = None
    COMPLEM: Optional[str] = None
    BAIRRO: Optional[str] = None
    CIDADE: Optional[str] = None
    UF: Optional[str] = None
    CEP: Optional[str] = None
    PAIS: Optional[str] = None
    OBS_CURTA: Optional[str] = None
    OBSERVACOES_LONGAS: Optional[str] = None
    SITUACAO: Optional[str] = None
    ID_RESP: Optional[str] = None


class AddressCreate(BaseModel):
    TIPO_END: str = "ENTREGA"
    ENDERECO: str
    NUMERO: str = "S/N"
    COMPLEM: Optional[str] = ""
    BAIRRO: str = ""
    CIDADE: str
    UF: str
    CEP: Optional[str] = ""
    PAIS: str = "Brasil"
    SITUACAO: str = "ATIVO"

