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

from services.scraper import buscar_e_salvar_ultimo_sorteio
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
