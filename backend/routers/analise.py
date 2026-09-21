import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from services.analise import (
    analise_frequencia,
    analise_paridade,
    analise_repetidas,
    ciclo_atual,
    gerar_sugestoes_fortes,
    situacao_dezenas_ultimo_concurso,
)
from services.exportacao import gerar_pdf_situacao_dezenas

router = APIRouter(prefix="/analise", tags=["analise"])


@router.get("/ciclo")
def get_ciclo(db: Session = Depends(get_db)):
    return ciclo_atual(db)


@router.get("/paridade")
def get_paridade(db: Session = Depends(get_db)):
    return analise_paridade(db)


@router.get("/repetidas")
def get_repetidas(db: Session = Depends(get_db)):
    return analise_repetidas(db)


@router.get("/frequencia")
def get_frequencia(db: Session = Depends(get_db)):
    return analise_frequencia(db)


@router.get("/radar")
def get_radar(db: Session = Depends(get_db)):
    return {
        "ciclo": ciclo_atual(db),
        "paridade": analise_paridade(db),
        "repetidas": analise_repetidas(db),
        "frequencia": analise_frequencia(db),
    }


# GET /relatorio-dezenas deve vir num path proprio (sem conflito com os
# demais, todos fixos) — gera o PDF de apoio usado no botao do Jogo Manual.
@router.get("/relatorio-dezenas")
def relatorio_dezenas_pdf(db: Session = Depends(get_db)):
    """
    Gera um PDF com a situação estatística das 25 dezenas em relação ao
    último concurso salvo (sequência ativa/chama para as sorteadas,
    atraso/sequência anterior para as que não saíram, e a classificação
    de frequência de cada uma) — material de apoio para o usuário
    estudar antes de montar um jogo no Jogo Manual.
    """
    situacao = situacao_dezenas_ultimo_concurso(db)
    if situacao["numero_concurso"] is None:
        raise HTTPException(status_code=404, detail="Nenhum sorteio cadastrado ainda")

    ciclo = ciclo_atual(db)
    sugestoes = gerar_sugestoes_fortes(situacao)
    pdf_bytes = gerar_pdf_situacao_dezenas(situacao, ciclo, sugestoes)

    nome_arquivo = f"lotofacil-situacao-dezenas-concurso-{situacao['numero_concurso']}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
