from sqlalchemy.orm import Session

import models


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
