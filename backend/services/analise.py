import random
from sqlalchemy.orm import Session

import models


FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
CENTRO = {7, 8, 9, 12, 13, 14, 17, 18, 19}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MULTIPLOS_3 = {3, 6, 9, 12, 15, 18, 21, 24}

_PARIDADES_VALIDAS = frozenset({(8, 7), (7, 8), (9, 6), (6, 9)})  # (impares, pares)


def ciclo_atual(db: Session) -> dict:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.asc())
        .all()
    )

    seen_in_cycle: set[int] = set()
    cycle_number = 1
    concursos_no_ciclo: list[int] = []

    for s in sorteios:
        concursos_no_ciclo.append(s.numero_concurso)
        for d in s.dezenas:
            seen_in_cycle.add(d)

        if len(seen_in_cycle) == 25:
            cycle_number += 1
            seen_in_cycle = set()
            concursos_no_ciclo = []

    all_dezenas = set(range(1, 26))
    return {
        "dezenas_pendentes": sorted(all_dezenas - seen_in_cycle),
        "dezenas_sorteadas": sorted(seen_in_cycle),
        "numero_ciclo_atual": cycle_number,
        "concursos_no_ciclo": concursos_no_ciclo,
    }


def analise_paridade(db: Session) -> list[dict]:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .all()
    )

    if not sorteios:
        return []

    total_sorteios = len(sorteios)
    count: dict[str, int] = {}
    last: dict[str, dict] = {}

    for i, s in enumerate(sorteios):
        comp = f"{s.total_pares}P/{s.total_impares}I"
        count[comp] = count.get(comp, 0) + 1
        if comp not in last:
            last[comp] = {"atraso": i, "concurso": s.numero_concurso}

    return sorted(
        [
            {
                "composicao": comp,
                "total_ocorrencias": count[comp],
                "percentual": round(count[comp] / total_sorteios * 100, 2),
                "atraso_atual": last[comp]["atraso"],
                "ultima_vez": last[comp]["concurso"],
            }
            for comp in count
        ],
        key=lambda x: x["composicao"],
    )


def analise_repetidas(db: Session) -> list[dict]:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .all()
    )

    if not sorteios:
        return []

    # Exclude the oldest sorteio — it has no predecessor to compare against
    min_concurso = min(s.numero_concurso for s in sorteios)

    count: dict[int, int] = {}
    last: dict[int, dict] = {}

    for i, s in enumerate(sorteios):
        if s.numero_concurso == min_concurso:
            continue
        qty = s.repetidas_anterior
        count[qty] = count.get(qty, 0) + 1
        if qty not in last:
            last[qty] = {"atraso": i, "concurso": s.numero_concurso}

    valid_total = sum(count.values())
    if valid_total == 0:
        return []

    return sorted(
        [
            {
                "quantidade_repetidas": qty,
                "total_ocorrencias": count[qty],
                "percentual": round(count[qty] / valid_total * 100, 2),
                "atraso_atual": last[qty]["atraso"],
                "is_ouro": qty in (8, 9, 10),
            }
            for qty in count
        ],
        key=lambda x: x["quantidade_repetidas"],
    )


def analise_frequencia(db: Session) -> list[dict]:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .limit(100)
        .all()
    )

    result = []
    for dezena in range(1, 26):
        freq_10 = sum(1 for s in sorteios[:10] if dezena in s.dezenas)
        freq_30 = sum(1 for s in sorteios[:30] if dezena in s.dezenas)
        freq_50 = sum(1 for s in sorteios[:50] if dezena in s.dezenas)
        freq_100 = sum(1 for s in sorteios if dezena in s.dezenas)

        # Expected frequency in 10 sorteios = 10 * 15 / 25 = 6
        if freq_10 >= 7:
            classificacao = "quente"
        elif freq_10 <= 4:
            classificacao = "fria"
        else:
            classificacao = "morna"

        result.append(
            {
                "dezena": dezena,
                "freq_10": freq_10,
                "freq_30": freq_30,
                "freq_50": freq_50,
                "freq_100": freq_100,
                "classificacao": classificacao,
            }
        )

    return result


def _calcular_stats(dezenas: list[int], ultimo_dezenas: list[int]) -> dict:
    s = set(dezenas)
    pares = sum(1 for d in dezenas if d % 2 == 0)
    return {
        "pares": pares,
        "impares": 15 - pares,
        "fibonacci": len(s & FIBONACCI),
        "moldura": len(s & MOLDURA),
        "centro": len(s & CENTRO),
        "primos": len(s & PRIMOS),
        "multiplos_3": len(s & MULTIPLOS_3),
        "repetidas_ultimo": len(s & set(ultimo_dezenas)),
        "soma": sum(dezenas),
    }


def _verificar_filtros(stats: dict, filtrar_repetidas: bool) -> list[str]:
    falhos = []
    if not (3 <= stats["fibonacci"] <= 5):
        falhos.append(f"Fibonacci fora do range (3–5): {stats['fibonacci']}")
    if not (9 <= stats["moldura"] <= 11):
        falhos.append(f"Moldura fora do range (9–11): {stats['moldura']}")
    if not (4 <= stats["primos"] <= 7):
        falhos.append(f"Primos fora do range (4–7): {stats['primos']}")
    if not (3 <= stats["multiplos_3"] <= 6):
        falhos.append(f"Múlt. de 3 fora do range (3–6): {stats['multiplos_3']}")
    if filtrar_repetidas and not (8 <= stats["repetidas_ultimo"] <= 10):
        falhos.append(f"Repetidas fora do range (8–10): {stats['repetidas_ultimo']}")
    if not (181 <= stats["soma"] <= 210):
        falhos.append(f"Soma fora do range (181–210): {stats['soma']}")
    if (stats["impares"], stats["pares"]) not in _PARIDADES_VALIDAS:
        falhos.append(f"Paridade inválida: {stats['impares']}I/{stats['pares']}P")
    return falhos


def _passa_filtros(dezenas: list[int], ultimo_dezenas: list[int], filtrar_repetidas: bool) -> bool:
    stats = _calcular_stats(dezenas, ultimo_dezenas)
    return len(_verificar_filtros(stats, filtrar_repetidas)) == 0


def analisar_jogo(dezenas: list[int], db: Session) -> dict:
    ultimo = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .first()
    )
    ultimo_dezenas = list(ultimo.dezenas) if ultimo else []
    filtrar_repetidas = bool(ultimo_dezenas)

    stats = _calcular_stats(dezenas, ultimo_dezenas)
    falhos = _verificar_filtros(stats, filtrar_repetidas)

    return {
        "dezenas": sorted(dezenas),
        **stats,
        "aprovado": len(falhos) == 0,
        "filtros_falhos": falhos,
    }


def gerar_propostas(db: Session) -> dict:
    ciclo = ciclo_atual(db)

    ultimo = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .first()
    )
    ultimo_dezenas = list(ultimo.dezenas) if ultimo else []
    filtrar_repetidas = bool(ultimo_dezenas)

    num_concursos = len(ciclo["concursos_no_ciclo"])
    ausentes = ciclo["dezenas_pendentes"]

    # Only fix ausentes when the cycle is mature and they fit within a jogo
    dezenas_fixas: list[int] = []
    if num_concursos >= 3 and len(ausentes) <= 15:
        dezenas_fixas = ausentes

    pool = [d for d in range(1, 26) if d not in dezenas_fixas]
    needed = 15 - len(dezenas_fixas)

    aprovados: list[list[int]] = []
    vistos: set[frozenset] = set()

    for _ in range(10_000):
        if len(aprovados) == 3:
            break
        complemento = random.sample(pool, needed)
        candidato = sorted(dezenas_fixas + complemento)
        fs = frozenset(candidato)
        if fs in vistos:
            continue
        vistos.add(fs)
        if _passa_filtros(candidato, ultimo_dezenas, filtrar_repetidas):
            aprovados.append(candidato)

    propostas = []
    for i, dezenas in enumerate(aprovados):
        stats = _calcular_stats(dezenas, ultimo_dezenas)
        propostas.append({
            "jogo": i + 1,
            "dezenas": dezenas,
            **stats,
            "estrategia": "Ciclo + 7 Filtros",
        })

    return {
        "ciclo_atual": ciclo["numero_ciclo_atual"],
        "concursos_no_ciclo": num_concursos,
        "ausentes_do_ciclo": ausentes,
        "dezenas_fixas": dezenas_fixas,
        "propostas": propostas,
    }
