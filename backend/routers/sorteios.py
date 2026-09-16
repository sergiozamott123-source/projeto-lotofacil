import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services.atualizacao import executar_atualizacao_e_conferencia, registrar_sorteio_manual
from services.importacao import importar_historico
from services.analise import gerar_propostas, analisar_jogo

router = APIRouter(prefix="/sorteios", tags=["sorteios"])


@router.get("/", response_model=List[schemas.SorteioOut])
def listar_sorteios(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Sorteio).order_by(models.Sorteio.numero_concurso.desc()).offset(skip).limit(limit).all()


@router.get("/atualizar")
def atualizar_sorteios(db: Session = Depends(get_db)):
    """
    Busca o resultado mais recente, salva no banco e — se for um concurso
    novo — confere sozinho todas as apostas pendentes e envia o e-mail de
    aviso. É este endpoint que o GitHub Actions chama todo dia (ver
    .github/workflows/atualizar-sorteios.yml), já que no plano gratuito o
    backend pode estar "dormindo" e o agendador interno sozinho não é
    suficiente.
    """
    try:
        resultado = executar_atualizacao_e_conferencia(db)
        return resultado
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar API da Caixa: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/registrar-manual")
def registrar_sorteio_manual_endpoint(payload: schemas.SorteioManualCreate, db: Session = Depends(get_db)):
    """
    Cadastra manualmente o resultado de um concurso — usado quando 'Atualizar
    Base' não consegue buscar sozinho (ex.: bloqueio da Caixa para
    servidores fora do Brasil). Segue o mesmo fluxo do automático: se for
    concurso novo, já confere as apostas pendentes e envia o e-mail.
    """
    try:
        return registrar_sorteio_manual(db, payload.numero_concurso, payload.data_sorteio, payload.dezenas)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/proposta", response_model=schemas.SorteioProposta)
def obter_proposta(db: Session = Depends(get_db)):
    try:
        return gerar_propostas(db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analisar", response_model=schemas.AnalisarJogoResponse)
def analisar_jogo_proprio(payload: schemas.AnalisarJogoRequest, db: Session = Depends(get_db)):
    try:
        return analisar_jogo(payload.dezenas, db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ultimo", response_model=schemas.SorteioUltimoOut)
def obter_ultimo_sorteio(db: Session = Depends(get_db)):
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .limit(2)
        .all()
    )
    if not sorteios:
        raise HTTPException(status_code=404, detail="Nenhum sorteio encontrado")
    ultimo = sorteios[0]
    anterior = sorteios[1] if len(sorteios) > 1 else None
    dezenas_repetidas = sorted(set(ultimo.dezenas) & set(anterior.dezenas)) if anterior else []
    return schemas.SorteioUltimoOut(
        **{c.key: getattr(ultimo, c.key) for c in ultimo.__table__.columns},
        numero_concurso_anterior=anterior.numero_concurso if anterior else None,
        dezenas_repetidas=dezenas_repetidas,
    )


@router.get("/{numero_concurso}", response_model=schemas.SorteioOut)
def obter_sorteio(numero_concurso: int, db: Session = Depends(get_db)):
    sorteio = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == numero_concurso).first()
    if not sorteio:
        raise HTTPException(status_code=404, detail="Sorteio não encontrado")
    return sorteio


@router.post("/", response_model=schemas.SorteioOut, status_code=201)
def criar_sorteio(sorteio: schemas.SorteioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == sorteio.numero_concurso).first()
    if existente:
        raise HTTPException(status_code=409, detail="Concurso já cadastrado")
    db_sorteio = models.Sorteio(**sorteio.model_dump())
    db.add(db_sorteio)
    db.commit()
    db.refresh(db_sorteio)
    return db_sorteio


@router.post("/importar", response_model=schemas.ImportacaoResult, status_code=200)
async def importar_sorteios(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".csv")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx ou .csv")

    conteudo = await file.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    try:
        resultado = await run_in_threadpool(
            importar_historico, conteudo, file.filename, db
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {exc}")

    return resultado
