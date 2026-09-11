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
class SorteioUltimoOut(SorteioOut):
    numero_concurso_anterior: Optional[int] = None
    dezenas_repetidas: List[int] = []
# --- Aposta ---
class ApostaBase(BaseModel):
    nome: str
    dezenas: List[int]
    numero_concurso_alvo: Optional[int] = None
    origem: OrigemEnum = OrigemEnum.manual
    @field_validator("dezenas")
    @classmethod
    def validar_dezenas(cls, v):
        if not (15 <= len(v) <= 20):
            raise ValueError("Uma aposta deve ter entre 15 e 20 dezenas (apostas especiais da Lotofácil vão até 20)")
        if not all(1 <= d <= 25 for d in v):
            raise ValueError("Dezenas devem estar entre 1 e 25")
        if len(set(v)) != len(v):
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
# --- Proposta de Apostas ---
class PropostaJogo(BaseModel):
    jogo: int
    dezenas: List[int]
    pares: int
    impares: int
    moldura: int
    centro: int
    repetidas_ultimo: int
    estrategia: str
    nivel: Optional[str] = None
    emoji: Optional[str] = None
    filtros_aprovados: Optional[int] = None
    total_filtros: Optional[int] = None
    filtros_falhos: List[str] = []
    inedito: bool = True
class SorteioProposta(BaseModel):
    ciclo_atual: int
    concursos_no_ciclo: int
    ausentes_do_ciclo: List[int]
    dezenas_fixas: List[int]
    propostas: List[PropostaJogo]
    resumo: Optional[dict] = None
    jogos_ja_sorteados_descartados: Optional[int] = None
# --- Análise de jogo próprio ---
class AnalisarJogoRequest(BaseModel):
    dezenas: List[int]
    @field_validator("dezenas")
    @classmethod
    def validar_dezenas(cls, v):
        if len(v) != 15:
            raise ValueError("Deve ter exatamente 15 dezenas")
        if not all(1 <= d <= 25 for d in v):
            raise ValueError("Dezenas devem estar entre 1 e 25")
        if len(set(v)) != 15:
            raise ValueError("Dezenas não podem se repetir")
        return sorted(v)
class AnalisarJogoResponse(BaseModel):
    dezenas: List[int]
    pares: int
    impares: int
    moldura: int
    centro: int
    repetidas_ultimo: int
    aprovado: bool
    filtros_falhos: List[str]
    nivel: Optional[str] = None
    filtros_aprovados: Optional[int] = None
    total_filtros: Optional[int] = None
    ja_sorteado: bool = False
    concurso_repetido: Optional[int] = None
# --- Importação ---
class ImportacaoResult(BaseModel):
    total_lidas: int
    total_inseridos: int
    total_ignorados: int
