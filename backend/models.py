from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class OrigemEnum(str, enum.Enum):
    manual = "manual"
    ia = "ia"


class Sorteio(Base):
    __tablename__ = "sorteios"

    id = Column(Integer, primary_key=True, index=True)
    numero_concurso = Column(Integer, unique=True, nullable=False, index=True)
    data_sorteio = Column(DateTime, nullable=False)
    dezenas = Column(ARRAY(Integer), nullable=False)
    total_pares = Column(Integer, nullable=False)
    total_impares = Column(Integer, nullable=False)
    repetidas_anterior = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Aposta(Base):
    __tablename__ = "apostas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    dezenas = Column(ARRAY(Integer), nullable=False)
    numero_concurso_alvo = Column(Integer, nullable=True)
    origem = Column(SAEnum(OrigemEnum), nullable=False, default=OrigemEnum.manual)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jogos = relationship("JogoRealizado", back_populates="aposta")


class JogoRealizado(Base):
    __tablename__ = "jogos_realizados"

    id = Column(Integer, primary_key=True, index=True)
    aposta_id = Column(Integer, ForeignKey("apostas.id"), nullable=False)
    numero_concurso = Column(Integer, nullable=False)
    dezenas_acertadas = Column(ARRAY(Integer), nullable=True)
    total_acertos = Column(Integer, nullable=False, default=0)
    premiado = Column(Boolean, nullable=False, default=False)
    faixa_premio = Column(String, nullable=True)
    conferido_em = Column(DateTime(timezone=True), server_default=func.now())

    aposta = relationship("Aposta", back_populates="jogos")
