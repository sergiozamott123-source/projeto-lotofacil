import json
import logging
import os

import anthropic
from sqlalchemy.orm import Session

import models
from services.analise import analise_frequencia, analise_paridade, analise_repetidas, ciclo_atual

logger = logging.getLogger(__name__)

PARIDADE_MAP = {
    "6P9I": (6, 9),
    "7P8I": (7, 8),
}

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def _ultima_dezenas(db: Session) -> list[int]:
    ultimo = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .first()
    )
    return list(ultimo.dezenas) if ultimo else []


def _validar_jogo(
    dezenas: list[int],
    ultima_dezenas: list[int],
    repetidas_alvo: int,
    paridade_alvo: str,
) -> tuple[bool, str]:
    if len(dezenas) != 15:
        return False, f"Esperado 15 dezenas, recebido {len(dezenas)}"
    if len(set(dezenas)) != 15:
        return False, "Dezenas duplicadas no jogo"
    if not all(1 <= d <= 25 for d in dezenas):
        return False, "Dezenas fora do range 1-25"
    if ultima_dezenas:
        repetidas = len(set(dezenas) & set(ultima_dezenas))
        if repetidas != repetidas_alvo:
            return False, f"Repetidas: esperado {repetidas_alvo}, obtido {repetidas}"
    if paridade_alvo != "auto" and paridade_alvo in PARIDADE_MAP:
        pares_esperados, _ = PARIDADE_MAP[paridade_alvo]
        pares = sum(1 for d in dezenas if d % 2 == 0)
        if pares != pares_esperados:
            return False, f"Paridade incorreta: {pares} pares (esperado {pares_esperados})"
    return True, ""


def _montar_contexto(
    frequencia: list[dict],
    ciclo: dict,
    paridade: list[dict],
    repetidas_stats: list[dict],
    ultima_dezenas: list[int],
    quantidade: int,
    repetidas_alvo: int,
    paridade_alvo: str,
) -> str:
    quentes = [d["dezena"] for d in frequencia if d["classificacao"] == "quente"]
    frias = [d["dezena"] for d in frequencia if d["classificacao"] == "fria"]

    par_str = (
        f"EXIGIDA: {paridade_alvo}"
        if paridade_alvo != "auto"
        else "LIVRE (escolha a mais frequente estatisticamente)"
    )

    par_stats = "\n".join(
        f"  {p['composicao']}: {p['percentual']}% ({p['total_ocorrencias']} vezes), "
        f"atraso: {p['atraso_atual']}"
        for p in sorted(paridade, key=lambda x: x["percentual"], reverse=True)[:6]
    )

    rep_stats = "\n".join(
        f"  {r['quantidade_repetidas']} repetidas: {r['percentual']}%, "
        f"atraso: {r['atraso_atual']}"
        for r in sorted(repetidas_stats, key=lambda x: x["quantidade_repetidas"])
    )

    return f"""## DADOS ESTATÍSTICOS — LOTOFÁCIL

### Último Sorteio (base para calcular repetidas)
Dezenas: {sorted(ultima_dezenas) if ultima_dezenas else "Sem dados"}

### Ciclo Atual (#{ciclo['numero_ciclo_atual']})
- Dezenas PENDENTES (alta prioridade): {ciclo['dezenas_pendentes']}
- Dezenas já sorteadas no ciclo: {ciclo['dezenas_sorteadas']}
- Concursos no ciclo: {len(ciclo['concursos_no_ciclo'])}

### Frequência (últimos 100 sorteios)
- Quentes (freq. alta): {quentes}
- Frias (freq. baixa): {frias}

### Paridade histórica
{par_stats}

### Repetidas históricas
{rep_stats}

## PARÂMETROS DA GERAÇÃO
- Jogos a gerar: {quantidade}
- Repetidas do último sorteio: EXATAMENTE {repetidas_alvo}
- Composição de paridade: {par_str}
- PRIORIZE dezenas pendentes do ciclo: {ciclo['dezenas_pendentes']}
"""


_SYSTEM_PROMPT = """Você é um especialista em análise estatística da Lotofácil. Gere jogos seguindo RIGOROSAMENTE os critérios fornecidos.

Regras do jogo:
- Cada jogo: 15 dezenas distintas, numeradas de 1 a 25
- "Repetidas" = dezenas presentes tanto no último sorteio quanto no jogo gerado
- "Pares" (P) = dezenas divisíveis por 2; "Ímpares" (I) = demais

Estratégia obrigatória:
1. Selecione EXATAMENTE o número de repetidas indicado, escolhendo as mais estratégicas do último sorteio
2. PRIORIZE dezenas pendentes do ciclo atual — maior probabilidade estatística de sair
3. Complete com dezenas quentes e estrategicamente escolhidas
4. Garanta a composição de paridade exigida (quando não for "auto")

FORMATO DE RESPOSTA: retorne APENAS um array JSON válido, sem markdown, sem texto extra:
[
  {"dezenas": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22, 23, 24, 25], "justificativa": "Justificativa concisa da estratégia usada"}
]

CRÍTICO: Cada jogo deve ter EXATAMENTE 15 dezenas ÚNICAS entre 1 e 25. Conte cuidadosamente antes de retornar."""


def gerar_jogos(
    db: Session,
    quantidade: int,
    repetidas_alvo: int,
    paridade_alvo: str,
) -> list[dict]:
    freq = analise_frequencia(db)
    ciclo = ciclo_atual(db)
    par = analise_paridade(db)
    rep = analise_repetidas(db)
    ultima = _ultima_dezenas(db)

    contexto = _montar_contexto(
        freq, ciclo, par, rep, ultima, quantidade, repetidas_alvo, paridade_alvo
    )

    client = _get_client()
    jogos_validos: list[dict] = []
    max_tentativas = 3

    for tentativa in range(1, max_tentativas + 1):
        faltam = quantidade - len(jogos_validos)
        if faltam <= 0:
            break

        msg = contexto
        if tentativa > 1:
            msg += (
                f"\n\nNOTA: Gere apenas {faltam} jogo(s) — os anteriores falharam na validação."
                f"\nLembre-se: EXATAMENTE {repetidas_alvo} dezenas do último sorteio "
                f"{sorted(ultima)} devem aparecer em cada jogo."
            )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": msg}],
            )
        except Exception as exc:
            logger.error("Tentativa %d: erro na API Anthropic: %s", tentativa, exc)
            continue

        raw = response.content[0].text.strip()

        if raw.startswith("```"):
            partes = raw.split("```")
            raw = partes[1] if len(partes) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            jogos_raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("Tentativa %d: JSON inválido: %s | raw=%r", tentativa, exc, raw[:300])
            continue

        if not isinstance(jogos_raw, list):
            logger.warning("Tentativa %d: resposta não é uma lista", tentativa)
            continue

        for jogo in jogos_raw:
            if len(jogos_validos) >= quantidade:
                break
            dezenas_raw = jogo.get("dezenas", [])
            try:
                dezenas = sorted(int(d) for d in dezenas_raw)
            except (TypeError, ValueError) as exc:
                logger.warning("Tentativa %d: dezenas inválidas %s: %s", tentativa, dezenas_raw, exc)
                continue

            valido, motivo = _validar_jogo(dezenas, ultima, repetidas_alvo, paridade_alvo)
            if valido:
                jogos_validos.append({
                    "dezenas": dezenas,
                    "justificativa": jogo.get("justificativa", ""),
                })
                logger.info("Tentativa %d: jogo válido: %s", tentativa, dezenas)
            else:
                logger.warning("Tentativa %d: jogo inválido (%s): %s", tentativa, motivo, dezenas)

    if len(jogos_validos) < quantidade:
        raise ValueError(
            f"Apenas {len(jogos_validos)} de {quantidade} jogos puderam ser validados "
            f"após {max_tentativas} tentativas."
        )

    return jogos_validos[:quantidade]
