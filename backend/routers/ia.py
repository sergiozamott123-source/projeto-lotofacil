from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

import models
from database import get_db
from services.gerador import gerar_jogos

router = APIRouter(prefix="/ia", tags=["ia"])


class GerarJogosRequest(BaseModel):
    quantidade: int = 1
    repetidas: int = 9
    paridade: str = "auto"
    salvar: bool = False

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("quantidade deve ser entre 1 e 10")
        return v

    @field_validator("repetidas")
    @classmethod
    def validar_repetidas(cls, v: int) -> int:
        if v not in (8, 9, 10):
            raise ValueError("repetidas deve ser 8, 9 ou 10")
        return v

    @field_validator("paridade")
    @classmethod
    def validar_paridade(cls, v: str) -> str:
        if v not in ("6P9I", "7P8I", "auto"):
            raise ValueError("paridade deve ser '6P9I', '7P8I' ou 'auto'")
        return v


class JogoGerado(BaseModel):
    dezenas: list[int]
    justificativa: str
    aposta_id: Optional[int] = None


@router.post("/gerar-jogos", response_model=list[JogoGerado])
def endpoint_gerar_jogos(
    request: GerarJogosRequest,
    db: Session = Depends(get_db),
) -> list[JogoGerado]:
    try:
        jogos = gerar_jogos(
            db=db,
            quantidade=request.quantidade,
            repetidas_alvo=request.repetidas,
            paridade_alvo=request.paridade,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar jogos com IA: {exc}")

    resultado: list[JogoGerado] = []
    for i, jogo in enumerate(jogos, 1):
        aposta_id = None
        if request.salvar:
            aposta = models.Aposta(
                nome=f"IA-{request.repetidas}R/{request.paridade}-{i:02d}",
                dezenas=jogo["dezenas"],
                origem=models.OrigemEnum.ia,
            )
            db.add(aposta)
            db.commit()
            db.refresh(aposta)
            aposta_id = aposta.id

        resultado.append(
            JogoGerado(
                dezenas=jogo["dezenas"],
                justificativa=jogo["justificativa"],
                aposta_id=aposta_id,
            )
        )

    return resultado
