"""
Motor determinístico de geração de jogos.

Diferença em relação a services/gerador.py (que usa a API da Anthropic para
gerar e validar jogos via LLM): este motor é 100% combinatório/determinístico,
não depende de chamada de IA, é instantâneo e permite ao usuário escolher
livremente:
  - quantos jogos gerar (sem teto fixo);
  - a FAIXA de paridade desejada (não um valor único);
  - a FAIXA de repetidas em relação ao concurso anterior (não um valor único);
  - se o critério de ciclo (dezenas represadas) deve ser priorizado.

A lógica foi validada em 05/09/2026 contra os 3.779 concursos históricos e
contra os 800 fechamentos de ciclo do histórico, sem falhas — inclusive no
caso de borda em que o concurso mais recente fecha o ciclo exatamente.
"""
from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

import models
from services.analise import MOLDURA, carregar_combinacoes_historicas

UNIVERSO = set(range(1, 26))
IMPAR = {n for n in UNIVERSO if n % 2 == 1}
PAR = UNIVERSO - IMPAR


@dataclass
class CriteriosGeracao:
    paridade_min: int = 6
    paridade_max: int = 9
    repetidas_min: int = 8
    repetidas_max: int = 10
    usar_ciclo: bool = True
    evitar_ja_sorteados: bool = True

    def validar(self) -> None:
        if not (0 <= self.paridade_min <= self.paridade_max <= 15):
            raise ValueError("Faixa de paridade inválida (use valores entre 0 e 15, min <= max).")
        if not (0 <= self.repetidas_min <= self.repetidas_max <= 15):
            raise ValueError("Faixa de repetidas inválida (use valores entre 0 e 15, min <= max).")


def _carregar_sorteios(db: Session) -> list[dict]:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.asc())
        .all()
    )
    return [
        {"concurso": s.numero_concurso, "dezenas": tuple(sorted(s.dezenas))}
        for s in sorteios
    ]


def diagnosticar(sorteios: list[dict]) -> dict:
    """Frequência, atraso e dezenas represadas do ciclo aberto."""
    if not sorteios:
        raise ValueError("Banco sem sorteios cadastrados — rode a atualização/importação primeiro.")

    freq: dict[int, int] = defaultdict(int)
    for s in sorteios:
        for n in s["dezenas"]:
            freq[n] += 1

    last_seen_idx: dict[int, int] = {}
    for i, s in enumerate(sorteios):
        for n in s["dezenas"]:
            last_seen_idx[n] = i
    atraso = {n: (len(sorteios) - 1 - last_seen_idx.get(n, -1)) for n in UNIVERSO}

    seen: set[int] = set()
    cycle_start_idx = 0
    for i, s in enumerate(sorteios):
        seen |= set(s["dezenas"])
        if seen == UNIVERSO:
            seen = set()
            cycle_start_idx = i + 1
    seen_atual: set[int] = set()
    for s in sorteios[cycle_start_idx:]:
        seen_atual |= set(s["dezenas"])
    represadas = sorted(UNIVERSO - seen_atual)

    return {"frequencia": dict(freq), "atraso": atraso, "represadas": represadas}


def _plano_do_jogo(R: int, E: int, pool_a_even: int, pool_a_odd: int,
                    pool_b_even: int, pool_b_odd: int) -> tuple[int, int, int, int]:
    """
    Dado R (repetidas do concurso anterior) e E (total de pares no jogo),
    devolve (a_even, a_odd, b_even, b_odd): quantas pares/ímpares vêm do
    concurso anterior (a_*) e quantas vêm do conjunto de "novas" (b_*).
    Levanta ValueError se a combinação não couber nos pools disponíveis.
    """
    lo = max(0, R - pool_a_odd, E - pool_b_even, R + E - 15)
    hi = min(pool_a_even, R, E, R + E - (15 - pool_b_odd))
    candidatos = list(range(lo, hi + 1))
    if not candidatos:
        raise ValueError(f"Combinação inviável para R={R}, E={E} com os pools disponíveis.")
    a_even = candidatos[len(candidatos) // 2]
    a_odd = R - a_even
    b_even = E - a_even
    b_odd = (15 - R) - b_even
    return a_even, a_odd, b_even, b_odd


def _distribuir(valores_possiveis: list[int], n: int) -> list[int]:
    if not valores_possiveis:
        raise ValueError("Faixa de critério vazia.")
    ciclo = itertools.cycle(valores_possiveis)
    return [next(ciclo) for _ in range(n)]


def gerar_jogos(db: Session, n_jogos: int, criterios: CriteriosGeracao) -> list[dict]:
    if n_jogos < 1:
        raise ValueError("n_jogos deve ser >= 1")
    criterios.validar()

    sorteios = _carregar_sorteios(db)
    diag = diagnosticar(sorteios)
    ultimo = set(sorteios[-1]["dezenas"])
    complemento = UNIVERSO - ultimo

    # represadas normalmente é subconjunto do complemento; no instante em que o
    # último concurso fechou o ciclo anterior, represadas = as 25 dezenas — por
    # isso interseccionamos: as "novas" de um jogo nunca podem repetir dezena
    # do último concurso.
    pool_ciclo = (set(diag["represadas"]) & complemento) if criterios.usar_ciclo else None
    pool_ciclo = pool_ciclo if pool_ciclo else None

    ultimo_odd = sorted(ultimo & IMPAR)
    ultimo_even = sorted(ultimo & PAR)
    completo_novas_odd = sorted(complemento & IMPAR)
    completo_novas_even = sorted(complemento & PAR)
    ciclo_novas_odd = sorted(pool_ciclo & IMPAR) if pool_ciclo else []
    ciclo_novas_even = sorted(pool_ciclo & PAR) if pool_ciclo else []

    reps_alvo = _distribuir(list(range(criterios.repetidas_min, criterios.repetidas_max + 1)), n_jogos)
    pares_alvo = _distribuir(list(range(criterios.paridade_min, criterios.paridade_max + 1)), n_jogos)

    usage_ultimo: dict[int, int] = defaultdict(int)
    usage_novas: dict[int, int] = defaultdict(int)

    def escolher(pool, k, usage, tie_key):
        pool_ordenado = sorted(pool, key=lambda n: (usage[n], -tie_key(n)))
        chosen = pool_ordenado[:k]
        for n in chosen:
            usage[n] += 1
        return chosen

    freq_key = lambda n: diag["frequencia"].get(n, 0)
    atraso_key = lambda n: diag["atraso"].get(n, 0)

    historicas = carregar_combinacoes_historicas(db) if criterios.evitar_ja_sorteados else {}

    jogos = []
    vistos: set[tuple] = set()
    for R, E in zip(reps_alvo, pares_alvo):
        ciclo_relaxado = False
        if pool_ciclo:
            try:
                a_even, a_odd, b_even, b_odd = _plano_do_jogo(
                    R, E, len(ultimo_even), len(ultimo_odd), len(ciclo_novas_even), len(ciclo_novas_odd)
                )
                novas_even, novas_odd = ciclo_novas_even, ciclo_novas_odd
            except ValueError:
                novas_even, novas_odd = completo_novas_even, completo_novas_odd
                ciclo_relaxado = True
                a_even, a_odd, b_even, b_odd = _plano_do_jogo(
                    R, E, len(ultimo_even), len(ultimo_odd), len(novas_even), len(novas_odd)
                )
        else:
            novas_even, novas_odd = completo_novas_even, completo_novas_odd
            a_even, a_odd, b_even, b_odd = _plano_do_jogo(
                R, E, len(ultimo_even), len(ultimo_odd), len(novas_even), len(novas_odd)
            )

        rep_evens = escolher(ultimo_even, a_even, usage_ultimo, freq_key)
        rep_odds = escolher(ultimo_odd, a_odd, usage_ultimo, freq_key)
        new_evens = escolher(novas_even, b_even, usage_novas, atraso_key)
        new_odds = escolher(novas_odd, b_odd, usage_novas, atraso_key)

        jogo = tuple(sorted(rep_evens + rep_odds + new_evens + new_odds))
        assert len(jogo) == 15 and len(set(jogo)) == 15, "erro interno: jogo malformado"

        tentativas = 0
        while (jogo in vistos or frozenset(jogo) in historicas) and tentativas < 5:
            rep_evens = escolher(ultimo_even, a_even, usage_ultimo, lambda n: -freq_key(n))
            jogo = tuple(sorted(rep_evens + rep_odds + new_evens + new_odds))
            tentativas += 1
        vistos.add(jogo)

        jogos.append({
            "dezenas": list(jogo),
            "pares": len(set(jogo) & PAR),
            "impares": len(set(jogo) & IMPAR),
            "moldura": len(set(jogo) & MOLDURA),
            "repetidas_concurso_anterior": len(set(jogo) & ultimo),
            "represadas_usadas": sorted(set(jogo) & set(diag["represadas"])),
            "ciclo_relaxado": ciclo_relaxado,
            "ja_sorteado_antes": frozenset(jogo) in historicas,
        })
    return jogos
