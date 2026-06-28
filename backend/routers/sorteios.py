import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas
from services.scraper import buscar_e_salvar_ultimo_sorteio
from services.importacao import importar_historico

router = APIRouter(prefix="/sorteios", tags=["sorteios"])


@router.get("/", response_model=List[schemas.SorteioOut])
def listar_sorteios(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Sorteio).order_by(models.Sorteio.numero_concurso.desc()).offset(skip).limit(limit).all()


@router.get("/atualizar")
def atualizar_sorteios(db: Session = Depends(get_db)):
    try:
        resultado = buscar_e_salvar_ultimo_sorteio(db)
        return resultado
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar API da Caixa: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
