import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import models

logger = logging.getLogger(__name__)

CAIXA_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"
FALLBACK_URL = "https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://loterias.caixa.gov.br/",
    "Origin": "https://loterias.caixa.gov.br",
}


def _normalizar_caixa(data: dict) -> dict:
    """Normaliza a resposta da API oficial da Caixa."""
    return {
        "numero": int(data["numero"]),
        "data_apuracao": datetime.strptime(data["dataApuracao"], "%d/%m/%Y"),
        "dezenas": sorted(int(d) for d in data["dezenasSorteadasOrdemSorteio"]),
    }


def _normalizar_fallback(data: dict) -> dict:
    """Normaliza a resposta da API alternativa (loteriascaixa-api)."""
    return {
        "numero": int(data["concurso"]),
        "data_apuracao": datetime.strptime(data["data"], "%d/%m/%Y"),
        "dezenas": sorted(int(d) for d in data["dezenas"]),
    }


def _buscar_dados_sorteio() -> dict:
    """
    Tenta buscar o sorteio mais recente, na ordem:
    1. API oficial da Caixa (pode falhar com 403 em servidores fora do Brasil)
    2. API alternativa (loteriascaixa-api)
    """
    try:
        response = httpx.get(CAIXA_URL, timeout=15, headers=HEADERS)
        response.raise_for_status()
        logger.info("Dados obtidos direto da Caixa.")
        return _normalizar_caixa(response.json())
    except httpx.HTTPStatusError as e:
        logger.warning("Caixa bloqueou a requisição (status %s). Tentando fallback...", e.response.status_code)
    except Exception as e:
        logger.warning("Erro ao consultar a Caixa diretamente: %s. Tentando fallback...", e)

    response = httpx.get(FALLBACK_URL, timeout=15)
    response.raise_for_status()
    logger.info("Dados obtidos da API alternativa (fallback).")
    return _normalizar_fallback(response.json())


def _calcular_stats(dezenas: list[int], anterior: list[int] | None) -> dict:
    total_pares = sum(1 for d in dezenas if d % 2 == 0)
    total_impares = 15 - total_pares
    repetidas = len(set(dezenas) & set(anterior)) if anterior else 0
    return {
        "total_pares": total_pares,
        "total_impares": total_impares,
        "repetidas_anterior": repetidas,
    }



def recalcular_repetidas_seguinte(db: Session, numero_concurso: int) -> None:
    """Depois de inserir o concurso N, ajusta `repetidas_anterior` do N+1
    se ele já existir no banco. Isso acontece quando um concurso entra
    "atrasado" e preenche um buraco na sequência (ex.: #3805 cadastrado
    depois do #3806): o N+1 foi gravado sem ter com quem comparar e ficou
    com repetidas = 0. Recebe a sessão já com o N salvo e faz o commit."""
    atual = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == numero_concurso).first()
    seguinte = db.query(models.Sorteio).filter(models.Sorteio.numero_concurso == numero_concurso + 1).first()
    if not atual or not seguinte:
        return
    novo = len(set(seguinte.dezenas) & set(atual.dezenas))
    if seguinte.repetidas_anterior != novo:
        logger.info(
            "Concurso %d: repetidas_anterior corrigido de %d para %d (buraco preenchido pelo %d).",
            seguinte.numero_concurso, seguinte.repetidas_anterior, novo, numero_concurso,
        )
        seguinte.repetidas_anterior = novo
        db.commit()


def buscar_e_salvar_ultimo_sorteio(db: Session) -> dict:
    dados = _buscar_dados_sorteio()
    numero = dados["numero"]
    data_apuracao = dados["data_apuracao"]
    dezenas = dados["dezenas"]

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
    if anterior is None and numero > 1:
        logger.warning(
            "Concurso %d inserido, mas o %d não está no banco — repetidas ficará 0 "
            "até o %d ser cadastrado (o cadastro dele corrige este valor sozinho).",
            numero, numero - 1, numero - 1,
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
    recalcular_repetidas_seguinte(db, numero)
    return {
        "status": "inserido",
        "numero_concurso": numero,
        "dezenas": dezenas,
        **stats,
    }
