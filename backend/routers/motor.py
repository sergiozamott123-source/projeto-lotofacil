from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models
from services.motor import CriteriosGeracao, gerar_jogos

router = APIRouter(prefix="/motor", tags=["motor"])


class GerarJogosFlexRequest(BaseModel):
    n_jogos: int = 6
    paridade_min: int = 6
    paridade_max: int = 9
    repetidas_min: int = 8
    repetidas_max: int = 10
    usar_ciclo: bool = True
    evitar_ja_sorteados: bool = True
    salvar: bool = False
    concurso_alvo: Optional[int] = None

    @field_validator("n_jogos")
    @classmethod
    def validar_n_jogos(cls, v: int) -> int:
        if not 1 <= v <= 100:
            raise ValueError("n_jogos deve ser entre 1 e 100")
        return v


class JogoGeradoFlex(BaseModel):
    dezenas: List[int]
    pares: int
    impares: int
    moldura: int
    repetidas_concurso_anterior: int
    represadas_usadas: List[int]
    ciclo_relaxado: bool
    ja_sorteado_antes: bool
    aposta_id: Optional[int] = None


@router.post("/gerar", response_model=List[JogoGeradoFlex])
def endpoint_gerar_jogos_flex(
    request: GerarJogosFlexRequest,
    db: Session = Depends(get_db),
) -> List[JogoGeradoFlex]:
    criterios = CriteriosGeracao(
        paridade_min=request.paridade_min,
        paridade_max=request.paridade_max,
        repetidas_min=request.repetidas_min,
        repetidas_max=request.repetidas_max,
        usar_ciclo=request.usar_ciclo,
        evitar_ja_sorteados=request.evitar_ja_sorteados,
    )
    try:
        jogos = gerar_jogos(db, request.n_jogos, criterios)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    resultado: List[JogoGeradoFlex] = []
    for i, jogo in enumerate(jogos, 1):
        aposta_id = None
        if request.salvar:
            aposta = models.Aposta(
                nome=f"MOTOR-{i:02d}-{jogo['repetidas_concurso_anterior']}R-{jogo['pares']}P{jogo['impares']}I",
                dezenas=jogo["dezenas"],
                numero_concurso_alvo=request.concurso_alvo,
                origem=models.OrigemEnum.ia,
            )
            db.add(aposta)
            db.commit()
            db.refresh(aposta)
            aposta_id = aposta.id

        resultado.append(JogoGeradoFlex(**jogo, aposta_id=aposta_id))

    return resultado
