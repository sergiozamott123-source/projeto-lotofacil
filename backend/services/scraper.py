import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)

CAIXA_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"


def _calcular_stats(dezenas: list[int], anterior: list[int] | None) -> dict:
    total_pares = sum(1 for d in dezenas if d % 2 == 0)
    total_impares = 15 - total_pares
    repetidas = len(set(dezenas) & set(anterior)) if anterior else 0
    return {
        "total_pares": total_pares,
        "total_impares": total_impares,
        "repetidas_anterior": repetidas,
    }


def buscar_e_salvar_ultimo_sorteio(db: Session) -> dict:
    response = httpx.get(CAIXA_URL, timeout=15)
    response.raise_for_status()
    data = response.json()

    numero = int(data["numero"])
    data_apuracao = datetime.strptime(data["dataApuracao"], "%d/%m/%Y")
    dezenas = sorted(int(d) for d in data["dezenasSorteadasOrdemSorteio"])

    existente = db.query(models.Sorteio).filter(
        models.Sorteio.numero_concurso == numero
    ).first()
    if existente:
        logger.info("Concurso %d já existe no banco.", numero)
        return {"status": "ja_existe", "numero_concurso": numero}

    anterior = (
        db.query(models.Sorteio)
        .filter(models.Sorteio.numero_concurso == numero - 1)
        .first()
    )
    stats = _calcular_stats(dezenas, anterior.dezenas if anterior else None)

    sorteio = models.Sorteio(
        numero_concurso=numero,
        data_sorteio=data_apuracao,
        dezenas=dezenas,
        **stats,
    )
    db.add(sorteio)
    db.commit()
    db.refresh(sorteio)

    logger.info("Concurso %d inserido com sucesso.", numero)
    return {
        "status": "inserido",
        "numero_concurso": numero,
        "dezenas": dezenas,
        **stats,
    }
