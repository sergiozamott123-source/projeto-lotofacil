import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
import models
import schemas
from services.analise import analise_pos_jogo_individual, analise_pos_jogo_geral
from services.conferencia import conferir_pendentes, conferir_pendentes_e_notificar, FAIXAS_PREMIO
from services.exportacao import gerar_pdf_apostas, gerar_pdf_pos_jogo_individual, gerar_pdf_pos_jogo_geral

router = APIRouter(prefix="/apostas", tags=["apostas"])


class AtualizarConcursoAlvo(BaseModel):
    numero_concurso_alvo: int


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


# GET /exportar-pdf deve vir antes de GET /{aposta_id} para evitar ambiguidade
@router.get("/exportar-pdf")
def exportar_apostas_pdf(numero_concurso_alvo: Optional[int] = None, db: Session = Depends(get_db)):
    """Gera um PDF com a lista de apostas (todas, ou filtradas por concurso
    alvo) para o usuário imprimir ou levar até a lotérica."""
    query = db.query(models.Aposta)
    if numero_concurso_alvo is not None:
        query = query.filter(models.Aposta.numero_concurso_alvo == numero_concurso_alvo)
    apostas = query.order_by(models.Aposta.created_at.desc()).all()

    if not apostas:
        raise HTTPException(status_code=404, detail="Nenhuma aposta encontrada para exportar")

    pdf_bytes = gerar_pdf_apostas(apostas, numero_concurso_alvo)

    nome_arquivo = (
        f"lotofacil-jogos-concurso-{numero_concurso_alvo}.pdf"
        if numero_concurso_alvo
        else "lotofacil-meus-jogos.pdf"
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


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


@router.patch("/{aposta_id}/concurso-alvo", response_model=schemas.ApostaOut)
def corrigir_concurso_alvo(aposta_id: int, dados: AtualizarConcursoAlvo, db: Session = Depends(get_db)):
    """Corrige o concurso-alvo de uma aposta já cadastrada (ex.: erro de
    digitação ao lançar o jogo — como registrar o concurso 3784 quando o
    certo era 3785). Se a aposta já havia sido conferida contra o
    concurso-alvo antigo, essa conferência (agora inválida) é apagada; o
    usuário deve conferir a aposta novamente depois, já contra o concurso
    correto."""
    aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")

    if dados.numero_concurso_alvo != aposta.numero_concurso_alvo:
        db.query(models.JogoRealizado).filter(
            models.JogoRealizado.aposta_id == aposta_id
        ).delete()
        aposta.numero_concurso_alvo = dados.numero_concurso_alvo

    db.commit()
    db.refresh(aposta)
    return aposta


# --- Pós-jogo: análise crítica de apostas já conferidas contra o resultado
# oficial — o par, olhando pra trás, do relatório de situação das dezenas
# (pré-jogo) em routers/analise.py. Individual (por aposta) e geral (todas
# as apostas conferidas de um concurso).

@router.get("/{aposta_id}/pos-jogo")
def pos_jogo_individual(aposta_id: int, db: Session = Depends(get_db)):
    analise = analise_pos_jogo_individual(db, aposta_id)
    if analise is None:
        aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
        if not aposta:
            raise HTTPException(status_code=404, detail="Aposta não encontrada")
        raise HTTPException(
            status_code=409,
            detail="Esta aposta ainda não foi conferida — confira-a antes de ver a análise pós-jogo.",
        )
    return analise


@router.get("/{aposta_id}/pos-jogo/pdf")
def pos_jogo_individual_pdf(aposta_id: int, db: Session = Depends(get_db)):
    analise = analise_pos_jogo_individual(db, aposta_id)
    if analise is None:
        aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
        if not aposta:
            raise HTTPException(status_code=404, detail="Aposta não encontrada")
        raise HTTPException(
            status_code=409,
            detail="Esta aposta ainda não foi conferida — confira-a antes de gerar a análise pós-jogo.",
        )
    pdf_bytes = gerar_pdf_pos_jogo_individual(analise)
    nome_arquivo = f"lotofacil-pos-jogo-aposta-{aposta_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@router.get("/pos-jogo-geral/{numero_concurso}")
def pos_jogo_geral(numero_concurso: int, db: Session = Depends(get_db)):
    analise = analise_pos_jogo_geral(db, numero_concurso)
    if analise is None:
        raise HTTPException(status_code=404, detail=f"Concurso {numero_concurso} não encontrado na base")
    return analise


@router.get("/pos-jogo-geral/{numero_concurso}/pdf")
def pos_jogo_geral_pdf(numero_concurso: int, db: Session = Depends(get_db)):
    analise = analise_pos_jogo_geral(db, numero_concurso)
    if analise is None:
        raise HTTPException(status_code=404, detail=f"Concurso {numero_concurso} não encontrado na base")
    pdf_bytes = gerar_pdf_pos_jogo_geral(analise)
    nome_arquivo = f"lotofacil-pos-jogo-concurso-{numero_concurso}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@router.delete("/{aposta_id}", status_code=204)
def deletar_aposta(aposta_id: int, db: Session = Depends(get_db)):
    aposta = db.query(models.Aposta).filter(models.Aposta.id == aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")
    db.delete(aposta)
    db.commit()
