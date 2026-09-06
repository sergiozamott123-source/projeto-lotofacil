from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
import models
import schemas
from services.conferencia import conferir_pendentes, conferir_pendentes_e_notificar, FAIXAS_PREMIO

router = APIRouter(prefix="/apostas", tags=["apostas"])


class ConferirResult(BaseModel):
    aposta_id: int
    numero_concurso: int
    dezenas_apostadas: List[int]
    dezenas_sorteadas: List[int]
    dezenas_acertadas: List[int]
    total_acertos: int
    premiado: bool
    faixa_premio: Optional[str]


class ConferirTodasResult(BaseModel):
    total_conferidas: int
    total_premiadas: int
    detalhes: List[ConferirResult]


class DistribuicaoFaixa(BaseModel):
    faixa: str
    total: int


class ResumoApostas(BaseModel):
    total_apostas: int
    total_conferidas: int
    total_premiadas: int
    melhor_resultado: Optional[int]
    distribuicao_faixas: List[DistribuicaoFaixa]


def _executar_conferencia(aposta: models.Aposta, db: Session) -> tuple[models.JogoRealizado, models.Sorteio]:
    if aposta.numero_concurso_alvo is None:
        raise HTTPException(status_code=400, detail="Aposta não tem concurso alvo definido")

    sorteio = db.query(models.Sorteio).filter(
        models.Sorteio.numero_concurso == aposta.numero_concurso_alvo
    ).first()

    if not sorteio:
        raise HTTPException(
            status_code=404,
            detail=f"Concurso {aposta.numero_concurso_alvo} ainda não disponível na base",
        )

    acertadas = sorted(set(aposta.dezenas) & set(sorteio.dezenas))
    total = len(acertadas)
    premiado = total >= 11
    faixa = FAIXAS_PREMIO.get(total) if premiado else None

    jogo = models.JogoRealizado(
        aposta_id=aposta.id,
        numero_concurso=sorteio.numero_concurso,
        dezenas_acertadas=acertadas,
        total_acertos=total,
        premiado=premiado,
        faixa_premio=faixa,
    )
    db.add(jogo)
    return jogo, sorteio


# GET /resumo deve vir antes de GET /{aposta_id} para evitar ambiguidade
@router.get("/resumo", response_model=ResumoApostas)
def resumo_apostas(db: Session = Depends(get_db)):
    total_apostas = db.query(func.count(models.Aposta.id)).scalar() or 0
    total_conferidas = db.query(func.count(models.JogoRealizado.id)).scalar() or 0
    total_premiadas = (
        db.query(func.count(models.JogoRealizado.id))
        .filter(models.JogoRealizado.premiado == True)
        .scalar() or 0
    )
    melhor = db.query(func.max(models.JogoRealizado.total_acertos)).scalar()

    faixas_raw = (
        db.query(models.JogoRealizado.faixa_premio, func.count(models.JogoRealizado.id))
        .filter(models.JogoRealizado.faixa_premio.isnot(None))
        .group_by(models.JogoRealizado.faixa_premio)
        .all()
    )

    return ResumoApostas(
        total_apostas=total_apostas,
        total_conferidas=total_conferidas,
        total_premiadas=total_premiadas,
        melhor_resultado=melhor,
        distribuicao_faixas=[DistribuicaoFaixa(faixa=f, total=c) for f, c in faixas_raw],
    )


@router.get("/", response_model=List[schemas.ApostaOut])
def listar_apostas(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Aposta).order_by(models.Aposta.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{aposta_id}", response_model=schemas.ApostaOut)
def obter_aposta(aposta_id: int, db: Session = Depends(get_db)):
    aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")
    return aposta


@router.post("/", response_model=schemas.ApostaOut, status_code=201)
def criar_aposta(aposta: schemas.ApostaCreate, db: Session = Depends(get_db)):
    db_aposta = models.Aposta(**aposta.model_dump())
    db.add(db_aposta)
    db.commit()
    db.refresh(db_aposta)
    return db_aposta


# POST /conferir-todas deve vir antes de POST /{aposta_id}/conferir
@router.post("/conferir-todas", response_model=ConferirTodasResult)
def conferir_todas_apostas(db: Session = Depends(get_db)):
    """
    Conferência manual, sob demanda (o botão "conferir agora" do painel).
    Usa a MESMA lógica que roda sozinha após cada atualização automática
    (services/conferencia.py) — a diferença é que aqui não dispara e-mail,
    já que o usuário está conferindo ativamente, na hora.
    """
    resultados = conferir_pendentes(db)

    detalhes = [
        ConferirResult(
            aposta_id=r.aposta_id,
            numero_concurso=r.numero_concurso,
            dezenas_apostadas=r.dezenas_apostadas,
            dezenas_sorteadas=r.dezenas_sorteadas,
            dezenas_acertadas=r.dezenas_acertadas,
            total_acertos=r.total_acertos,
            premiado=r.premiado,
            faixa_premio=r.faixa_premio,
        )
        for r in resultados
    ]

    return ConferirTodasResult(
        total_conferidas=len(detalhes),
        total_premiadas=sum(1 for d in detalhes if d.premiado),
        detalhes=detalhes,
    )


@router.post("/conferir-e-notificar", response_model=ConferirTodasResult)
def conferir_todas_e_notificar(db: Session = Depends(get_db)):
    """
    Igual ao /conferir-todas, mas dispara o e-mail de aviso mesmo sem uma
    atualizacao automatica de sorteio ter acontecido. Util para testar o
    envio de e-mail, ou para reenviar o aviso manualmente se precisar.
    """
    resultados = conferir_pendentes_e_notificar(db)

    detalhes = [
        ConferirResult(
            aposta_id=r.aposta_id,
            numero_concurso=r.numero_concurso,
            dezenas_apostadas=r.dezenas_apostadas,
            dezenas_sorteadas=r.dezenas_sorteadas,
            dezenas_acertadas=r.dezenas_acertadas,
            total_acertos=r.total_acertos,
            premiado=r.premiado,
            faixa_premio=r.faixa_premio,
        )
        for r in resultados
    ]

    return ConferirTodasResult(
        total_conferidas=len(detalhes),
        total_premiadas=sum(1 for d in detalhes if d.premiado),
        detalhes=detalhes,
    )


@router.post("/{aposta_id}/conferir", response_model=schemas.JogoRealizadoOut)
def conferir_aposta(aposta_id: int, db: Session = Depends(get_db)):
    aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")

    ja_conferida = db.query(models.JogoRealizado).filter(
        models.JogoRealizado.aposta_id == aposta_id
    ).first()
    if ja_conferida:
        raise HTTPException(status_code=409, detail="Aposta já foi conferida anteriormente")

    jogo, _ = _executar_conferencia(aposta, db)
    db.commit()
    db.refresh(jogo)
    return jogo


@router.delete("/{aposta_id}", status_code=204)
def deletar_aposta(aposta_id: int, db: Session = Depends(get_db)):
    aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")
    db.delete(aposta)
    db.commit()
