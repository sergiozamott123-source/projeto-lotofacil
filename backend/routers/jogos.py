from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/jogos", tags=["jogos"])


@router.get("/", response_model=List[schemas.JogoRealizadoOut])
def listar_jogos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.JogoRealizado).order_by(models.JogoRealizado.conferido_em.desc()).offset(skip).limit(limit).all()


@router.get("/aposta/{aposta_id}", response_model=List[schemas.JogoRealizadoOut])
def jogos_por_aposta(aposta_id: int, db: Session = Depends(get_db)):
    return db.query(models.JogoRealizado).filter(models.JogoRealizado.aposta_id == aposta_id).all()


@router.post("/", response_model=schemas.JogoRealizadoOut, status_code=201)
def registrar_jogo(jogo: schemas.JogoRealizadoCreate, db: Session = Depends(get_db)):
    aposta = db.query(models.Aposta).filter(models.Aposta.id == jogo.aposta_id).first()
    if not aposta:
        raise HTTPException(status_code=404, detail="Aposta não encontrada")
    db_jogo = models.JogoRealizado(**jogo.model_dump())
    db.add(db_jogo)
    db.commit()
    db.refresh(db_jogo)
    return db_jogo
