from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.analise import (
    analise_frequencia,
    analise_paridade,
    analise_repetidas,
    ciclo_atual,
)

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
