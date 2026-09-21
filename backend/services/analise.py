import random
from sqlalchemy.orm import Session

import models


MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
CENTRO = {7, 8, 9, 12, 13, 14, 17, 18, 19}

_PARIDADES_VALIDAS = frozenset({(8, 7), (7, 8), (9, 6), (6, 9)})


def carregar_combinacoes_historicas(db: Session) -> dict[frozenset, int]:
    """Retorna um dicionário {combinação: numero_concurso} de tudo que já foi sorteado."""
    sorteios = db.query(models.Sorteio.numero_concurso, models.Sorteio.dezenas).all()
    return {frozenset(dezenas): numero for numero, dezenas in sorteios}


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


def _classificar_frequencia(freq_10: int) -> str:
    if freq_10 >= 7:
        return "quente"
    elif freq_10 <= 4:
        return "fria"
    return "morna"


def _frequencias_dezena(sorteios: list, dezena: int) -> dict:
    """Calcula freq_10/30/50/100 e a classificação (fria/morna/quente) de
    uma dezena, a partir de uma lista de sorteios já ordenada do mais
    recente para o mais antigo. Compartilhada por `analise_frequencia` e
    por `situacao_dezenas_ultimo_concurso`, pra manter a mesma régua."""
    freq_10 = sum(1 for s in sorteios[:10] if dezena in s.dezenas)
    freq_30 = sum(1 for s in sorteios[:30] if dezena in s.dezenas)
    freq_50 = sum(1 for s in sorteios[:50] if dezena in s.dezenas)
    freq_100 = sum(1 for s in sorteios[:100] if dezena in s.dezenas)
    return {
        "freq_10": freq_10,
        "freq_30": freq_30,
        "freq_50": freq_50,
        "freq_100": freq_100,
        "classificacao": _classificar_frequencia(freq_10),
    }


def analise_frequencia(db: Session) -> list[dict]:
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .limit(100)
        .all()
    )

    return [
        {"dezena": dezena, **_frequencias_dezena(sorteios, dezena)}
        for dezena in range(1, 26)
    ]


def situacao_dezenas_ultimo_concurso(db: Session) -> dict:
    """
    Situação estatística de cada uma das 25 dezenas em relação ao último
    concurso salvo — base do relatório em PDF do Jogo Manual.

    - Sorteadas no último concurso: sequência ativa (nº de concursos
      seguidos, incluindo o último, saindo sem falhar) e se está "em
      chama" (sequência >= 3, o mesmo critério já usado no frontend).
    - Não sorteadas: atraso atual (concursos seguidos sem sair, contando
      a partir do último) e o tamanho da sequência que tinham logo antes
      de parar de sair.

    Ambos os grupos também trazem a classificação de frequência (fria/
    morna/quente) já usada em `analise_frequencia`, pra dar o quadro
    completo numa tacada só.
    """
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .limit(100)
        .all()
    )
    if not sorteios:
        return {
            "numero_concurso": None,
            "data_sorteio": None,
            "total_pares": None,
            "total_impares": None,
            "repetidas_anterior": None,
            "sorteadas": [],
            "nao_sorteadas": [],
        }

    ultimo = sorteios[0]
    sorteadas_set = set(ultimo.dezenas)
    nao_sorteadas_set = set(range(1, 26)) - sorteadas_set

    sorteadas = []
    for dezena in sorted(sorteadas_set):
        streak = 0
        for s in sorteios:
            if dezena in s.dezenas:
                streak += 1
            else:
                break
        sorteadas.append({
            "dezena": dezena,
            "sequencia_ativa": streak,
            "em_chama": streak >= 3,
            **_frequencias_dezena(sorteios, dezena),
        })

    nao_sorteadas = []
    for dezena in sorted(nao_sorteadas_set):
        atraso = 0
        for s in sorteios:
            if dezena in s.dezenas:
                break
            atraso += 1
        sequencia_anterior = 0
        for s in sorteios[atraso:]:
            if dezena in s.dezenas:
                sequencia_anterior += 1
            else:
                break
        nao_sorteadas.append({
            "dezena": dezena,
            "atraso_atual": atraso,
            "sequencia_anterior": sequencia_anterior,
            **_frequencias_dezena(sorteios, dezena),
        })

    return {
        "numero_concurso": ultimo.numero_concurso,
        "data_sorteio": ultimo.data_sorteio,
        "total_pares": ultimo.total_pares,
        "total_impares": ultimo.total_impares,
        "repetidas_anterior": ultimo.repetidas_anterior,
        "sorteadas": sorteadas,
        "nao_sorteadas": nao_sorteadas,
    }


ETAPAS = [
    {"numero": 1, "nome": "Arranque", "inicio": 1, "fim": 5},
    {"numero": 2, "nome": "Metade inicial", "inicio": 6, "fim": 10},
    {"numero": 3, "nome": "Metade central", "inicio": 11, "fim": 15},
    {"numero": 4, "nome": "Metade final", "inicio": 16, "fim": 20},
    {"numero": 5, "nome": "Encerramento", "inicio": 21, "fim": 25},
]

# Cada etapa tem 5 dezenas; cada concurso sorteia 15 das 25 dezenas (60%).
# Por isso o "esperado" — sem nenhum viés — é de 3,0 dezenas de cada etapa
# por concurso. Serve só como referência neutra de comparação, não como
# alvo a perseguir.
_MEDIA_ESPERADA_POR_ETAPA = 3.0
_LIMIAR_DESVIO_TENDENCIA = 0.5  # abaixo disso, consideramos "equilibrada"


def analise_etapas(db: Session, n_concursos: int = 5) -> dict:
    """
    Divide as 25 dezenas em 5 etapas fixas de 5 dezenas cada (1-5, 6-10,
    11-15, 16-20, 21-25) — inspirado na ideia de "setores" de um circuito:
    em vez de olhar só pra dezena individual, dá pra ver como cada trecho
    da grade se comportou nos concursos mais recentes.

    Para os últimos `n_concursos` (padrão 5), calcula por etapa: quantas
    dezenas dela saíram em cada concurso, o total e a média no período, a
    comparação com o esperado neutro (3,0 dezenas/concurso, já que cada
    etapa tem 5 das 25 dezenas e cada concurso sorteia 60% delas), e quais
    dezenas dessa etapa mais se repetiram no período.

    É leitura descritiva do comportamento recente, no mesmo espírito das
    demais seções do relatório — não é sinal preditivo nem critério
    validado de composição (esses seguem sendo só paridade, repetidas e
    ciclo, documentados em criterios-e-jogos.md).
    """
    sorteios = (
        db.query(models.Sorteio)
        .order_by(models.Sorteio.numero_concurso.desc())
        .limit(n_concursos)
        .all()
    )
    if not sorteios:
        return {"concursos_considerados": [], "n_concursos": 0, "etapas": []}

    concursos_considerados = [s.numero_concurso for s in sorteios]  # mais recente primeiro
    n = len(sorteios)

    etapas_resultado = []
    for etapa in ETAPAS:
        faixa = set(range(etapa["inicio"], etapa["fim"] + 1))
        contagem_por_concurso = []
        contagem_dezenas: dict[int, int] = {}

        for s in sorteios:
            dezenas_na_faixa = sorted(set(s.dezenas) & faixa)
            contagem_por_concurso.append({
                "concurso": s.numero_concurso,
                "quantidade": len(dezenas_na_faixa),
                "dezenas": dezenas_na_faixa,
            })
            for d in dezenas_na_faixa:
                contagem_dezenas[d] = contagem_dezenas.get(d, 0) + 1

        total = sum(c["quantidade"] for c in contagem_por_concurso)
        media = round(total / n, 2)
        desvio = media - _MEDIA_ESPERADA_POR_ETAPA

        if desvio >= _LIMIAR_DESVIO_TENDENCIA:
            tendencia = "acima"
        elif desvio <= -_LIMIAR_DESVIO_TENDENCIA:
            tendencia = "abaixo"
        else:
            tendencia = "equilibrada"

        dezenas_recorrentes = sorted(
            ({"dezena": d, "vezes": v} for d, v in contagem_dezenas.items() if v >= 2),
            key=lambda x: (-x["vezes"], x["dezena"]),
        )

        etapas_resultado.append({
            "etapa": etapa["numero"],
            "nome": etapa["nome"],
            "inicio": etapa["inicio"],
            "fim": etapa["fim"],
            "contagem_por_concurso": contagem_por_concurso,
            "total": total,
            "media": media,
            "media_esperada": _MEDIA_ESPERADA_POR_ETAPA,
            "tendencia": tendencia,
            "dezenas_recorrentes": dezenas_recorrentes,
        })

    return {
        "concursos_considerados": concursos_considerados,
        "n_concursos": n,
        "media_esperada_por_concurso": _MEDIA_ESPERADA_POR_ETAPA,
        "etapas": etapas_resultado,
    }


def gerar_sugestoes_fortes(situacao: dict) -> list[dict]:
    """
    Combina os critérios já validados no projeto — paridade (`_PARIDADES_VALIDAS`),
    meta de repetidas do concurso anterior (8/9/10) e as dezenas quentes/em chama
    calculadas em `situacao_dezenas_ultimo_concurso` — pra sugerir até 3 apostas
    "fortes", como material de apoio consultivo pro Jogo Manual.

    Não é previsão: é uma seleção determinística dentro dos critérios já
    validados estatisticamente (ver `criterios-e-jogos.md`), priorizando as
    dezenas com sinal mais recente de "quente" em cada faixa. A divisão exata
    pares/ímpares entre "repete do último concurso" e "vem das que não saíram"
    reaproveita `_plano_do_jogo`, o mesmo solver combinatório já validado e em
    produção no Motor Estatístico (`services/motor.py`) — import local pra não
    criar dependência circular entre os dois módulos.
    """
    from services.motor import _plano_do_jogo, PAR, IMPAR

    sorteadas = situacao.get("sorteadas") or []
    nao_sorteadas = situacao.get("nao_sorteadas") or []
    if len(sorteadas) != 15 or len(nao_sorteadas) != 10:
        return []

    def prioridade_repetir(d: dict) -> tuple:
        return (
            1 if d["em_chama"] else 0,
            d["sequencia_ativa"],
            1 if d["classificacao"] == "quente" else 0,
            d["freq_10"],
        )

    def prioridade_nova(d: dict) -> tuple:
        return (
            1 if d["classificacao"] == "quente" else 0,
            d["sequencia_anterior"],
            d["freq_10"],
        )

    repetir_ordenado = sorted(sorteadas, key=prioridade_repetir, reverse=True)
    novas_ordenado = sorted(nao_sorteadas, key=prioridade_nova, reverse=True)

    repetir_even = [d for d in repetir_ordenado if d["dezena"] in PAR]
    repetir_odd = [d for d in repetir_ordenado if d["dezena"] in IMPAR]
    novas_even = [d for d in novas_ordenado if d["dezena"] in PAR]
    novas_odd = [d for d in novas_ordenado if d["dezena"] in IMPAR]

    # (repetidas_alvo, pares_alvo) — paridade alternando entre os dois pares
    # mais usados na metodologia validada (8P/7I e 7P/8I), repetidas cobrindo
    # a faixa 8/9/10 documentada em criterios-e-jogos.md.
    planos = [(8, 8), (9, 7), (10, 8)]

    sugestoes = []
    for repetidas_alvo, pares_alvo in planos:
        try:
            a_even, a_odd, b_even, b_odd = _plano_do_jogo(
                repetidas_alvo, pares_alvo,
                len(repetir_even), len(repetir_odd), len(novas_even), len(novas_odd),
            )
        except ValueError:
            continue  # combinação inviável com os dados atuais — pula essa sugestão

        escolhidas_repetir = repetir_even[:a_even] + repetir_odd[:a_odd]
        escolhidas_novas = novas_even[:b_even] + novas_odd[:b_odd]
        todas = escolhidas_repetir + escolhidas_novas
        dezenas = sorted(d["dezena"] for d in todas)

        quentes_incluidas = sorted(
            d["dezena"] for d in todas
            if d.get("em_chama") or d["classificacao"] == "quente"
        )

        sugestoes.append({
            "repetidas_alvo": repetidas_alvo,
            "dezenas": dezenas,
            "pares": sum(1 for d in dezenas if d in PAR),
            "impares": sum(1 for d in dezenas if d in IMPAR),
            "repetidas_reais": len(escolhidas_repetir),
            "quentes_incluidas": quentes_incluidas,
        })

    return sugestoes


def _calcular_stats(dezenas: list[int], ultimo_dezenas: list[int]) -> dict:
    s = set(dezenas)
    pares = sum(1 for d in dezenas if d % 2 == 0)
    return {
        "pares": pares,
        "impares": 15 - pares,
        "moldura": len(s & MOLDURA),
        "centro": len(s & CENTRO),
        "repetidas_ultimo": len(s & set(ultimo_dezenas)),
    }


def _contar_filtros_aprovados(stats: dict, filtrar_repetidas: bool) -> tuple[int, list[str]]:
    """Retorna (numero_filtros_aprovados, lista_de_filtros_falhos)"""
    falhos = []
    if not (9 <= stats["moldura"] <= 11):
        falhos.append(f"Moldura fora do range (9–11): {stats['moldura']}")
    if filtrar_repetidas and not (8 <= stats["repetidas_ultimo"] <= 10):
        falhos.append(f"Repetidas fora do range (8–10): {stats['repetidas_ultimo']}")
    if (stats["impares"], stats["pares"]) not in _PARIDADES_VALIDAS:
        falhos.append(f"Paridade inválida: {stats['impares']}I/{stats['pares']}P")

    total_filtros = 7 if filtrar_repetidas else 6
    aprovados = total_filtros - len(falhos)
    return aprovados, falhos


def _classificar_nivel(aprovados: int, total: int) -> str:
    percentual = aprovados / total
    if percentual == 1.0:
        return "ouro"
    elif percentual >= 0.71:  # 5 ou 6 de 7
        return "prata"
    elif percentual >= 0.43:  # 3 ou 4 de 7
        return "bronze"
    else:
        return "reprovado"


def _verificar_filtros(stats: dict, filtrar_repetidas: bool) -> list[str]:
    _, falhos = _contar_filtros_aprovados(stats, filtrar_repetidas)
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
    aprovados, falhos = _contar_filtros_aprovados(stats, filtrar_repetidas)
    total_filtros = 7 if filtrar_repetidas else 6
    nivel = _classificar_nivel(aprovados, total_filtros)

    # Verifica se essa combinação exata já foi sorteada alguma vez
    combinacoes_historicas = carregar_combinacoes_historicas(db)
    concurso_repetido = combinacoes_historicas.get(frozenset(dezenas))
    ja_sorteado = concurso_repetido is not None

    return {
        "dezenas": sorted(dezenas),
        **stats,
        "aprovado": len(falhos) == 0,
        "nivel": nivel,
        "filtros_aprovados": aprovados,
        "total_filtros": total_filtros,
        "filtros_falhos": falhos,
        "ja_sorteado": ja_sorteado,
        "concurso_repetido": concurso_repetido,
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
    total_filtros = 7 if filtrar_repetidas else 6

    # Carrega todas as combinações já sorteadas na história, pra garantir jogos inéditos
    combinacoes_historicas = carregar_combinacoes_historicas(db)

    num_concursos = len(ciclo["concursos_no_ciclo"])
    ausentes = ciclo["dezenas_pendentes"]

    dezenas_fixas: list[int] = []
    if num_concursos >= 3 and len(ausentes) <= 15:
        dezenas_fixas = ausentes

    pool = [d for d in range(1, 26) if d not in dezenas_fixas]
    needed = 15 - len(dezenas_fixas)

    ouro: list[tuple] = []
    prata: list[tuple] = []
    bronze: list[tuple] = []
    vistos: set[frozenset] = set()
    descartados_por_ja_sorteado = 0

    for _ in range(50_000):
        if len(ouro) >= 2 and len(prata) >= 2 and len(bronze) >= 2:
            break
        complemento = random.sample(pool, needed)
        candidato = sorted(dezenas_fixas + complemento)
        fs = frozenset(candidato)
        if fs in vistos:
            continue
        vistos.add(fs)

        # Descarta se essa combinação já saiu alguma vez na história da Lotofácil
        if fs in combinacoes_historicas:
            descartados_por_ja_sorteado += 1
            continue

        stats = _calcular_stats(candidato, ultimo_dezenas)
        aprovados, falhos = _contar_filtros_aprovados(stats, filtrar_repetidas)
        nivel = _classificar_nivel(aprovados, total_filtros)

        if nivel == "ouro" and len(ouro) < 2:
            ouro.append((candidato, stats, aprovados, falhos))
        elif nivel == "prata" and len(prata) < 2:
            prata.append((candidato, stats, aprovados, falhos))
        elif nivel == "bronze" and len(bronze) < 2:
            bronze.append((candidato, stats, aprovados, falhos))

    def formatar(jogos, nivel_nome, emoji):
        resultado = []
        for i, (dezenas, stats, aprovados, falhos) in enumerate(jogos):
            resultado.append({
                "jogo": i + 1,
                "dezenas": dezenas,
                **stats,
                "nivel": nivel_nome,
                "emoji": emoji,
                "filtros_aprovados": aprovados,
                "total_filtros": total_filtros,
                "filtros_falhos": falhos,
                "estrategia": f"{emoji} {nivel_nome} — {aprovados}/{total_filtros} filtros",
                "inedito": True,
            })
        return resultado

    propostas = (
        formatar(ouro, "Ouro", "🥇") +
        formatar(prata, "Prata", "🥈") +
        formatar(bronze, "Bronze", "🥉")
    )

    return {
        "ciclo_atual": ciclo["numero_ciclo_atual"],
        "concursos_no_ciclo": num_concursos,
        "ausentes_do_ciclo": ausentes,
        "dezenas_fixas": dezenas_fixas,
        "propostas": propostas,
        "resumo": {
            "ouro": len(ouro),
            "prata": len(prata),
            "bronze": len(bronze),
        },
        "jogos_ja_sorteados_descartados": descartados_por_ja_sorteado,
    }
