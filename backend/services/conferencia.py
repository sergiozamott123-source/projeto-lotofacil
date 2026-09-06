"""
Conferência de apostas — lógica compartilhada entre:
  - o endpoint manual (POST /apostas/conferir-todas), para quando o usuário
    quiser conferir na hora;
  - o job automático do scheduler, disparado logo depois que um novo
    concurso é inserido no banco — para que o usuário NUNCA precise lembrar
    de conferir: o sistema confere sozinho e avisa por e-mail.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

import models
from services.email_service import enviar_email_conferencia

logger = logging.getLogger(__name__)

FAIXAS_PREMIO = {
    11: "quadra",
    12: "quina",
    13: "sena",
    14: "quatorze",
    15: "sena máxima",
}


@dataclass
class ResultadoConferencia:
    aposta_id: int
    nome_aposta: str
    numero_concurso: int
    dezenas_apostadas: list[int]
    dezenas_sorteadas: list[int]
    dezenas_acertadas: list[int]
    total_acertos: int
    premiado: bool
    faixa_premio: str | None


def conferir_pendentes(db: Session) -> list[ResultadoConferencia]:
    """
    Confere todas as apostas com concurso alvo já disponível no banco e que
    ainda não têm um JogoRealizado associado. Grava o resultado (commit) e
    devolve os detalhes de cada uma — não envia notificação (ver
    `conferir_pendentes_e_notificar` para isso).
    """
    apostas_ja_conferidas = db.query(models.JogoRealizado.aposta_id).subquery()
    apostas_pendentes = (
        db.query(models.Aposta)
        .filter(
            models.Aposta.id.notin_(apostas_ja_conferidas),
            models.Aposta.numero_concurso_alvo.isnot(None),
        )
        .all()
    )

    resultados: list[ResultadoConferencia] = []
    for aposta in apostas_pendentes:
        sorteio = (
            db.query(models.Sorteio)
            .filter(models.Sorteio.numero_concurso == aposta.numero_concurso_alvo)
            .first()
        )
        if not sorteio:
            continue  # concurso alvo ainda não saiu / base não atualizada

        acertadas = sorted(set(aposta.dezenas) & set(sorteio.dezenas))
        total = len(acertadas)
        premiado = total >= 11
        faixa = FAIXAS_PREMIO.get(total) if premiado else None

        db.add(models.JogoRealizado(
            aposta_id=aposta.id,
            numero_concurso=sorteio.numero_concurso,
            dezenas_acertadas=acertadas,
            total_acertos=total,
            premiado=premiado,
            faixa_premio=faixa,
        ))
        resultados.append(ResultadoConferencia(
            aposta_id=aposta.id,
            nome_aposta=aposta.nome,
            numero_concurso=sorteio.numero_concurso,
            dezenas_apostadas=list(aposta.dezenas),
            dezenas_sorteadas=list(sorteio.dezenas),
            dezenas_acertadas=acertadas,
            total_acertos=total,
            premiado=premiado,
            faixa_premio=faixa,
        ))

    db.commit()
    return resultados


def conferir_pendentes_e_notificar(db: Session) -> list[ResultadoConferencia]:
    """Confere pendências e, se houver alguma, dispara e-mail de aviso.
    Nunca deixa uma falha no envio de e-mail derrubar a conferência em si —
    o resultado já foi salvo no banco antes de tentarmos notificar."""
    resultados = conferir_pendentes(db)
    if not resultados:
        return resultados

    try:
        enviar_email_conferencia(resultados)
    except Exception:
        logger.exception(
            "Conferência salva no banco (%d aposta(s)), mas o e-mail de aviso falhou.",
            len(resultados),
        )
    return resultados
