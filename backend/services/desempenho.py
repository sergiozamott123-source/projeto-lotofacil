"""
Desempenho e balanço financeiro das apostas — alimenta os dois cards do
Dashboard ("Meu desempenho" e "Balanço financeiro").

Regras (decididas com o Sérgio em 17/10/2026):
  - Só entram apostas simples de 15 dezenas. As de 17 dezenas foram cota de
    bolão de uma edição especial e ficam fora do cálculo.
  - Apostas com concurso-alvo absurdo (ex.: 8303, erro de digitação) ficam
    fora — só conta alvo até o último concurso + MARGEM_PENDENTES.
  - Meta: 11 acertos ou mais (o mínimo premiado).
  - Prêmios de 11, 12 e 13 acertos são fixos. Os de 14 e 15 variam a cada
    concurso (rateio): quando acontecerem, aparecem como "a confirmar" e
    não entram no total — melhor subestimar o ganho do que inventá-lo.
"""
from __future__ import annotations

from collections import defaultdict
from math import comb

from sqlalchemy import func
from sqlalchemy.orm import Session

import models

PRECO_APOSTA_15 = 3.50
PREMIOS_FIXOS = {11: 7.00, 12: 14.00, 13: 35.00}
META_ACERTOS = 11
MARGEM_PENDENTES = 3

# Chance de uma aposta de 15 dezenas fazer 11+ por puro acaso
# (hipergeométrica: 15 sorteadas entre 25). Serve de régua honesta.
_TOTAL = comb(25, 15)
CHANCE_META_ACASO = sum(comb(15, k) * comb(10, 15 - k) for k in range(META_ACERTOS, 16)) / _TOTAL


def calcular_desempenho(db: Session) -> dict:
    ultimo = db.query(func.max(models.Sorteio.numero_concurso)).scalar() or 0
    limite_alvo = ultimo + MARGEM_PENDENTES

    apostas = [
        a for a in db.query(models.Aposta)
        .filter(models.Aposta.numero_concurso_alvo.isnot(None))
        .all()
        if len(a.dezenas) == 15 and a.numero_concurso_alvo <= limite_alvo
    ]
    jogos = {
        j.aposta_id: j for j in db.query(models.JogoRealizado)
        .filter(models.JogoRealizado.aposta_id.in_([a.id for a in apostas] or [0]))
        .all()
    }

    por_concurso: dict[int, dict] = defaultdict(lambda: {
        "apostas": 0, "acertos": [], "gasto": 0.0, "ganho": 0.0, "a_confirmar": 0,
    })
    por_mes: dict[str, float] = defaultdict(float)
    distribuicao = defaultdict(int)
    pendentes = 0
    gasto_pendente = 0.0
    premios_a_confirmar = 0

    for a in apostas:
        mes = a.created_at.strftime("%Y-%m") if a.created_at else "?"
        por_mes[mes] += PRECO_APOSTA_15
        jogo = jogos.get(a.id)
        if jogo is None:
            pendentes += 1
            gasto_pendente += PRECO_APOSTA_15
            continue
        c = por_concurso[jogo.numero_concurso]
        c["apostas"] += 1
        c["gasto"] += PRECO_APOSTA_15
        c["acertos"].append(jogo.total_acertos)
        distribuicao[jogo.total_acertos] += 1
        if jogo.total_acertos in PREMIOS_FIXOS:
            c["ganho"] += PREMIOS_FIXOS[jogo.total_acertos]
        elif jogo.total_acertos >= 14:
            c["a_confirmar"] += 1
            premios_a_confirmar += 1

    concursos = []
    gasto_acum = ganho_acum = 0.0
    for numero in sorted(por_concurso):
        c = por_concurso[numero]
        gasto_acum += c["gasto"]
        ganho_acum += c["ganho"]
        concursos.append({
            "numero_concurso": numero,
            "apostas": c["apostas"],
            "melhor_acerto": max(c["acertos"]),
            "na_meta": sum(1 for x in c["acertos"] if x >= META_ACERTOS),
            "gasto": round(c["gasto"], 2),
            "ganho": round(c["ganho"], 2),
            "gasto_acumulado": round(gasto_acum, 2),
            "ganho_acumulado": round(ganho_acum, 2),
            "premios_a_confirmar": c["a_confirmar"],
        })

    conferidas = sum(distribuicao.values())
    na_meta = sum(n for k, n in distribuicao.items() if k >= META_ACERTOS)
    gasto_total = round(gasto_acum + gasto_pendente, 2)
    ganho_total = round(ganho_acum, 2)

    return {
        "meta_acertos": META_ACERTOS,
        "preco_aposta": PRECO_APOSTA_15,
        "premios_fixos": PREMIOS_FIXOS,
        "apostas_conferidas": conferidas,
        "apostas_na_meta": na_meta,
        "taxa_meta": round(na_meta / conferidas, 4) if conferidas else 0,
        "chance_meta_acaso": round(CHANCE_META_ACASO, 4),
        "melhor_acerto": max(distribuicao) if distribuicao else None,
        "distribuicao_acertos": [{"acertos": k, "apostas": distribuicao[k]} for k in sorted(distribuicao)],
        "concursos": concursos,
        "gasto_total": gasto_total,
        "ganho_total": ganho_total,
        "saldo": round(ganho_total - gasto_total, 2),
        "retorno_por_real": round(ganho_total / gasto_total, 2) if gasto_total else 0,
        "apostas_pendentes": pendentes,
        "gasto_pendente": round(gasto_pendente, 2),
        "premios_a_confirmar": premios_a_confirmar,
        "gasto_por_mes": [{"mes": m, "gasto": round(v, 2)} for m, v in sorted(por_mes.items())],
    }
