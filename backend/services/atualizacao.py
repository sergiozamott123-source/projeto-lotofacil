"""
Orquestra o ciclo completo de atualização: busca o resultado mais recente,
salva no banco e, se um concurso novo entrou, confere sozinho todas as
apostas pendentes e dispara o e-mail de aviso — tudo em uma chamada só.

Usado por:
  - scheduler.py (agendador interno, quando o processo está de pé);
  - routers/sorteios.py (endpoint GET /api/sorteios/atualizar), que é o que
    o GitHub Actions chama de fora — importante no plano gratuito, já que o
    Render "dorme" e o agendador interno não é confiável sozinho.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

import models
from services.scraper import buscar_e_salvar_ultimo_sorteio, _calcular_stats
from services.conferencia import conferir_pendentes_e_notificar

logger = logging.getLogger(__name__)


def executar_atualizacao_e_conferencia(db: Session) -> dict:
    resultado = buscar_e_salvar_ultimo_sorteio(db)

    conferencias = []
    if resultado.get("status") == "inserido":
        conferencias = conferir_pendentes_e_notificar(db)
        logger.info(
            "Concurso %s inserido -> %d aposta(s) conferida(s) automaticamente.",
            resultado.get("numero_concurso"), len(conferencias),
        )

    return {
        **resultado,
        "apostas_conferidas_automaticamente": len(conferencias),
        "apostas_premiadas": sum(1 for c in conferencias if c.premiado),
    }


def registrar_sorteio_manual(db: Session, numero_concurso: int, data_sorteio, dezenas: list[int]) -> dict:
    """Registra manualmente o resultado de um concurso — usado quando a
    busca automática não consegue (ex.: bloqueio da Caixa para servidores
    fora do Brasil e fontes de reserva desatualizadas). Segue o mesmo
    caminho de `buscar_e_salvar_ultimo_sorteio`: calcula pares/ímpares e
    repetidas em relação ao concurso anterior, salva e, se for um concurso
    novo, confere sozinho as apostas pendentes e dispara o e-mail de aviso.
    """
    existente = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == numero_concurso).first()
    if existente:
        logger.info("Concurso %d já existe no banco (cadastro manual ignorado).", numero_concurso)
        return {
            "status": "ja_existe",
            "numero_concurso": numero_concurso,
            "apostas_conferidas_automaticamente": 0,
            "apostas_premiadas": 0,
        }

    dezenas_ordenadas = sorted(dezenas)
    anterior = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == numero_concurso - 1).first()
    stats = _calcular_stats(dezenas_ordenadas, anterior.dezenas if anterior else None)

    sorteio = models.Sorteio(
        numero_concurso=numero_concurso,
        data_sorteio=data_sorteio,
        dezenas=dezenas_ordenadas,
        **stats,
    )
    db.add(sorteio)
    db.commit()
    db.refresh(sorteio)
    logger.info("Concurso %d inserido manualmente com sucesso.", numero_concurso)

    conferencias = conferir_pendentes_e_notificar(db)
    logger.info(
        "Concurso %s (manual) -> %d aposta(s) conferida(s) automaticamente.",
        numero_concurso, len(conferencias),
    )

    return {
        "status": "inserido",
        "numero_concurso": numero_concurso,
        "dezenas": dezenas_ordenadas,
        **stats,
        "apostas_conferidas_automaticamente": len(conferencias),
        "apostas_premiadas": sum(1 for c in conferencias if c.premiado),
    }
