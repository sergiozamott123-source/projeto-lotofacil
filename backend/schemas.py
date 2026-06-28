from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrigemEnum(str, Enum):
    manual = "manual"
    ia = "ia"


# --- Sorteio ---

class SorteioBase(BaseModel):
    numero_concurso: int
    data_sorteio: datetime
    dezenas: List[int]
    total_pares: int
    total_impares: int
    repetidas_anterior: int = 0

    @field_validator("dezenas")
    @classmethod
    def validar_dezenas(cls, v):
        if len(v) != 15:
            raise ValueError("Um sorteio deve ter exatamente 15 dezenas")
        if not all(1 <= d <= 25 for d in v):
            raise ValueError("Dezenas devem estar entre 1 e 25")
        return sorted(v)


class SorteioCreate(SorteioBase):
    pass


class SorteioOut(SorteioBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Aposta ---

class ApostaBase(BaseModel):
    nome: str
    dezenas: List[int]
    numero_concurso_alvo: Optional[int] = None
    origem: OrigemEnum = OrigemEnum.manual

    @field_validator("dezenas")
    @classmethod
    def validar_dezenas(cls, v):
        if len(v) != 15:
            raise ValueError("Uma aposta deve ter exatamente 15 dezenas")
        if not all(1 <= d <= 25 for d in v):
            raise ValueError("Dezenas devem estar entre 1 e 25")
        if len(set(v)) != 15:
            raise ValueError("Dezenas não podem se repetir")
        return sorted(v)


class ApostaCreate(ApostaBase):
    pass


class ApostaOut(ApostaBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- JogoRealizado ---

class JogoRealizadoBase(BaseModel):
    aposta_id: int
    numero_concurso: int
    dezenas_acertadas: Optional[List[int]] = None
    total_acertos: int = 0
    premiado: bool = False
    faixa_premio: Optional[str] = None


class JogoRealizadoCreate(JogoRealizadoBase):
    pass


class JogoRealizadoOut(JogoRealizadoBase):
    id: int
    conferido_em: datetime

    model_config = {"from_attributes": True}


# --- Importação ---

class ImportacaoResult(BaseModel):
    total_lidas: int
    total_inseridos: int
    total_ignorados: int
