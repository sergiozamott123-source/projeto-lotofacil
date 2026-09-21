"""
Geração de PDF com a lista de apostas do usuário — pensado para imprimir
ou levar até a lotérica na hora de registrar os jogos.
"""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)

ROXO = colors.HexColor("#6d28d9")
ROXO_CLARO = colors.HexColor("#f5f3ff")
CINZA = colors.HexColor("#64748b")
BORDA = colors.HexColor("#e2e8f0")

# Cores da classificação de frequência (fria/morna/quente) — mesma
# paleta usada nos cards do Dashboard e do Jogo Manual.
COR_QUENTE = colors.HexColor("#fdba74")
COR_FRIA = colors.HexColor("#93c5fd")
COR_MORNA = colors.HexColor("#f1f5f9")
COR_HEADER_TXT = colors.white

FAIXA_LABEL = {
    "quadra": "Quadra (11 acertos)",
    "quina": "Quina (12 acertos)",
    "sena": "Sena (13 acertos)",
    "quatorze": "Quatorze (14 acertos)",
    "sena máxima": "Sena Máxima (15 acertos)",
}


def _formatar_dezenas(dezenas: list[int]) -> str:
    return "  ".join(f"{d:02d}" for d in sorted(dezenas))


def _status_texto(aposta) -> str:
    jogo = aposta.jogos[0] if aposta.jogos else None
    if jogo is None:
        return "Pendente de conferência"
    if jogo.premiado:
        faixa = FAIXA_LABEL.get(jogo.faixa_premio, jogo.faixa_premio)
        return f"{jogo.total_acertos} acertos — {faixa}"
    return f"{jogo.total_acertos} acertos — não premiado"


def gerar_pdf_apostas(apostas: list, numero_concurso_alvo: int | None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="Lotofácil IA - Meus Jogos",
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloLotofacil", parent=styles["Heading1"], textColor=ROXO, fontSize=20, spaceAfter=2,
    )
    subtitulo_style = ParagraphStyle(
        "SubtituloLotofacil", parent=styles["Normal"], textColor=CINZA, fontSize=10, spaceAfter=16,
    )
    celula_style = ParagraphStyle("Celula", parent=styles["Normal"], fontSize=9, leading=13)
    celula_dezenas_style = ParagraphStyle(
        "CelulaDezenas", parent=styles["Normal"], fontSize=9, leading=13, fontName="Courier",
    )
    cabecalho_style = ParagraphStyle(
        "Cabecalho", parent=styles["Normal"], fontSize=9, textColor=colors.white, fontName="Helvetica-Bold",
    )
    rodape_style = ParagraphStyle("Rodape", parent=styles["Normal"], fontSize=8, textColor=CINZA, spaceBefore=16)

    elementos = []
    elementos.append(Paragraph("Lotofácil IA — Meus Jogos", titulo_style))
    gerado_em = datetime.now().strftime("%d/%m/%Y às %H:%M")
    if numero_concurso_alvo:
        subtitulo = f"Concurso alvo: {numero_concurso_alvo}  •  Gerado em {gerado_em}  •  {len(apostas)} jogo(s)"
    else:
        subtitulo = f"Todas as apostas  •  Gerado em {gerado_em}  •  {len(apostas)} jogo(s)"
    elementos.append(Paragraph(subtitulo, subtitulo_style))

    cabecalho = [
        Paragraph("Jogo", cabecalho_style),
        Paragraph("Concurso", cabecalho_style),
        Paragraph("Dezenas", cabecalho_style),
        Paragraph("Status", cabecalho_style),
    ]
    dados = [cabecalho]
    for aposta in apostas:
        origem_txt = "IA" if aposta.origem.value == "ia" else "Manual"
        nome_cel = Paragraph(
            f"{aposta.nome}<br/><font size=7 color='#94a3b8'>{origem_txt} • {len(aposta.dezenas)} dezenas</font>",
            celula_style,
        )
        concurso_cel = Paragraph(
            str(aposta.numero_concurso_alvo) if aposta.numero_concurso_alvo else "—", celula_style
        )
        dezenas_cel = Paragraph(_formatar_dezenas(aposta.dezenas), celula_dezenas_style)
        status_cel = Paragraph(_status_texto(aposta), celula_style)
        dados.append([nome_cel, concurso_cel, dezenas_cel, status_cel])

    tabela = Table(dados, colWidths=[4.2 * cm, 2.2 * cm, 6.8 * cm, 4.3 * cm], repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ROXO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROXO_CLARO]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDA),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elementos.append(tabela)
    elementos.append(Spacer(1, 12))
    elementos.append(
        Paragraph(
            "Gerado automaticamente pelo Lotofácil IA. Este documento é apenas um registro pessoal dos "
            "jogos e não substitui o volante oficial da Caixa Econômica Federal.",
            rodape_style,
        )
    )

    doc.build(elementos)
    return buffer.getvalue()


def _cor_classificacao(nome: str):
    return {"quente": COR_QUENTE, "fria": COR_FRIA, "morna": COR_MORNA}.get(nome, colors.white)


def _fmt_dezena(n: int) -> str:
    return f"{n:02d}"


def _tabela_sorteadas(sorteadas: list[dict]) -> Table:
    cabecalho = [
        "Dezena", "Sequência ativa\n(concursos seguidos)", "Chama\n(seq. >= 3)",
        "Classificação", "Freq.\núlt. 10", "Freq.\núlt. 30", "Freq.\núlt. 50", "Freq.\núlt. 100",
    ]
    dados = [cabecalho]
    cores_linha = []
    for d in sorteadas:
        dados.append([
            _fmt_dezena(d["dezena"]),
            str(d["sequencia_ativa"]),
            "Sim" if d["em_chama"] else "-",
            d["classificacao"].capitalize(),
            str(d["freq_10"]), str(d["freq_30"]), str(d["freq_50"]), str(d["freq_100"]),
        ])
        cores_linha.append(_cor_classificacao(d["classificacao"]))

    col_widths = [1.7*cm, 3.5*cm, 2.2*cm, 2.6*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.9*cm]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), ROXO),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_HEADER_TXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.6, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 3.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
    ]
    for i, c in enumerate(cores_linha, start=1):
        estilo.append(("BACKGROUND", (3, i), (3, i), c))
    t.setStyle(TableStyle(estilo))
    return t


def _tabela_nao_sorteadas(nao_sorteadas: list[dict]) -> Table:
    cabecalho = [
        "Dezena", "Atraso atual\n(concursos sem sair)", "Sequência anterior\n(antes de parar)",
        "Classificação", "Freq.\núlt. 10", "Freq.\núlt. 30", "Freq.\núlt. 50", "Freq.\núlt. 100",
    ]
    dados = [cabecalho]
    cores_linha = []
    for d in nao_sorteadas:
        dados.append([
            _fmt_dezena(d["dezena"]),
            str(d["atraso_atual"]),
            str(d["sequencia_anterior"]),
            d["classificacao"].capitalize(),
            str(d["freq_10"]), str(d["freq_30"]), str(d["freq_50"]), str(d["freq_100"]),
        ])
        cores_linha.append(_cor_classificacao(d["classificacao"]))

    col_widths = [1.7*cm, 3.5*cm, 3.5*cm, 2.6*cm, 1.7*cm, 1.7*cm, 1.7*cm, 1.8*cm]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), ROXO),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_HEADER_TXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.6),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.6, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 3.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
    ]
    for i, c in enumerate(cores_linha, start=1):
        estilo.append(("BACKGROUND", (3, i), (3, i), c))
    t.setStyle(TableStyle(estilo))
    return t


def _legenda_classificacao() -> Table:
    style = ParagraphStyle("LegendaPdf", fontName="Helvetica", fontSize=8.3, leading=12, textColor=CINZA)
    dados = [[
        Paragraph("Quente", style),
        Paragraph("Morna", style),
        Paragraph("Fria", style),
    ]]
    t = Table(dados, colWidths=[3*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), COR_QUENTE),
        ("BACKGROUND", (1, 0), (1, 0), COR_MORNA),
        ("BACKGROUND", (2, 0), (2, 0), COR_FRIA),
        ("BOX", (0, 0), (0, 0), 0.6, BORDA),
        ("BOX", (1, 0), (1, 0), 0.6, BORDA),
        ("BOX", (2, 0), (2, 0), 0.6, BORDA),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _tabela_sugestoes(sugestoes: list[dict]) -> Table:
    cabecalho = [
        "Sugestão", "Dezenas do jogo", "Pares /\nÍmpares", "Repetidas\ndo último", "Dezenas quentes incluídas",
    ]
    dados = [cabecalho]
    for i, s in enumerate(sugestoes, start=1):
        dezenas_fmt = " ".join(_fmt_dezena(d) for d in s["dezenas"])
        quentes_fmt = ", ".join(_fmt_dezena(d) for d in s["quentes_incluidas"]) if s["quentes_incluidas"] else "—"
        dados.append([
            str(i),
            dezenas_fmt,
            f"{s['pares']}P / {s['impares']}I",
            str(s["repetidas_reais"]),
            quentes_fmt,
        ])

    col_widths = [1.6*cm, 10.8*cm, 2.4*cm, 2.4*cm, 6.0*cm]
    t = Table(dados, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ROXO),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_HEADER_TXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.6),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (0, -1), 10),
        ("FONTNAME", (1, 1), (1, -1), "Courier-Bold"),
        ("FONTSIZE", (1, 1), (1, -1), 9.5),
        ("FONTNAME", (2, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (2, 1), (-1, -1), 8.8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.6, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (4, 1), (4, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROXO_CLARO]),
    ]))
    return t


def _construir_destaques(situacao: dict, ciclo: dict) -> str:
    """Monta o parágrafo de destaques dinamicamente a partir dos dados
    calculados — nunca com números fixos, pra continuar correto em
    qualquer concurso futuro."""
    partes = []

    sorteadas = situacao["sorteadas"]
    if sorteadas:
        campeao = max(sorteadas, key=lambda d: d["sequencia_ativa"])
        if campeao["sequencia_ativa"] >= 3:
            partes.append(
                f"a dezena {_fmt_dezena(campeao['dezena'])} está na maior sequência ativa "
                f"({campeao['sequencia_ativa']} concursos seguidos)"
            )

    rompidas = sorted(
        (d for d in situacao["nao_sorteadas"] if d["sequencia_anterior"] >= 5),
        key=lambda d: -d["sequencia_anterior"],
    )[:3]
    if rompidas:
        desc = "; ".join(f"{_fmt_dezena(d['dezena'])} ({d['sequencia_anterior']} concursos)" for d in rompidas)
        partes.append(f"encerraram sequências longas exatamente neste concurso: {desc}")

    pendentes = ciclo.get("dezenas_pendentes") or []
    if pendentes:
        lista = ", ".join(_fmt_dezena(d) for d in pendentes)
        partes.append(
            f"as dezenas {lista} são as represadas do ciclo atual "
            f"(#{ciclo['numero_ciclo_atual']}), sem sair desde o início dele"
        )

    if not partes:
        return "Nenhum destaque estatístico relevante identificado para este concurso."
    return "Destaques do concurso: " + "; ".join(partes) + "."


def gerar_pdf_situacao_dezenas(situacao: dict, ciclo: dict, sugestoes: list[dict] | None = None) -> bytes:
    """Gera o relatório em PDF com a situação estatística das 25 dezenas
    em relação ao último concurso salvo — material de apoio para o
    usuário estudar antes de montar um jogo no Jogo Manual. Quando
    `sugestoes` é passado (ver `services.analise.gerar_sugestoes_fortes`),
    inclui também uma seção de recomendação combinando paridade, meta de
    repetidas e dezenas quentes/em chama."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        title="Lotofácil IA - Situação das Dezenas",
        leftMargin=1.4 * cm, rightMargin=1.4 * cm, topMargin=1.0 * cm, bottomMargin=1.0 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloSituacao", parent=styles["Heading1"], textColor=ROXO, fontSize=18, spaceAfter=2,
    )
    subtitulo_style = ParagraphStyle(
        "SubtituloSituacao", parent=styles["Normal"], textColor=CINZA, fontSize=10, spaceAfter=10,
    )
    secao_style = ParagraphStyle(
        "SecaoSituacao", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=5,
        textColor=colors.HexColor("#1e293b"),
    )
    corpo_style = ParagraphStyle(
        "CorpoSituacao", parent=styles["Normal"], fontSize=9.2, leading=13, textColor=colors.HexColor("#334155"),
    )
    nota_style = ParagraphStyle("NotaSituacao", parent=styles["Normal"], fontSize=8.3, leading=11.5, textColor=CINZA)
    nota_negrito_style = ParagraphStyle(
        "NotaSituacaoNegrito", parent=nota_style, fontName="Helvetica-Bold",
    )

    numero = situacao["numero_concurso"]
    gerado_em = datetime.now().strftime("%d/%m/%Y às %H:%M")

    elementos = []
    elementos.append(Paragraph("LotoIA — Situação Estatística das Dezenas", titulo_style))
    elementos.append(Paragraph(
        f"Referência: concurso nº {numero} &nbsp;|&nbsp; Ciclo atual: #{ciclo['numero_ciclo_atual']} "
        f"&nbsp;|&nbsp; Gerado em {gerado_em}",
        subtitulo_style,
    ))
    elementos.append(HRFlowable(width="100%", thickness=1, color=BORDA))

    elementos.append(Paragraph(
        f"O concurso #{numero} saiu com {situacao['total_pares']} pares / {situacao['total_impares']} ímpares"
        + (f" e {situacao['repetidas_anterior']} dezenas repetidas em relação ao concurso anterior."
           if situacao["repetidas_anterior"] is not None else ".")
        + " A tabela abaixo resume, para cada uma das 25 dezenas, como ela vinha se comportando nos sorteios "
        "mais recentes: sequência de acertos consecutivos, atraso atual e classificação de frequência "
        "(fria / morna / quente).",
        corpo_style,
    ))

    sorteadas = situacao["sorteadas"]
    nao_sorteadas = situacao["nao_sorteadas"]
    dezenas_sorteadas_fmt = ", ".join(_fmt_dezena(d["dezena"]) for d in sorteadas)
    dezenas_nao_sorteadas_fmt = ", ".join(_fmt_dezena(d["dezena"]) for d in nao_sorteadas)

    elementos.append(Paragraph(f"1. As {len(sorteadas)} dezenas sorteadas no concurso #{numero}", secao_style))
    elementos.append(Paragraph(
        f"{dezenas_sorteadas_fmt} — \"Sequência ativa\" é o número de concursos seguidos (incluindo o "
        f"#{numero}) em que a dezena vem saindo sem falhar; a partir de 3 concursos seguidos ela é "
        "marcada como \"chama\" no sistema.",
        corpo_style,
    ))
    elementos.append(Spacer(1, 6))
    elementos.append(_tabela_sorteadas(sorteadas))

    elementos.append(Paragraph(f"2. As {len(nao_sorteadas)} dezenas que não saíram no concurso #{numero}", secao_style))
    elementos.append(Paragraph(
        f"{dezenas_nao_sorteadas_fmt} — \"Atraso atual\" é a quantidade de concursos seguidos sem sair "
        f"(contando a partir do #{numero}); \"Sequência anterior\" é o tamanho da sequência de acertos "
        "que a dezena tinha logo antes de parar de sair.",
        corpo_style,
    ))
    elementos.append(Spacer(1, 6))
    elementos.append(_tabela_nao_sorteadas(nao_sorteadas))

    elementos.append(Spacer(1, 10))
    elementos.append(_legenda_classificacao())

    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(_construir_destaques(situacao, ciclo), nota_negrito_style))
    elementos.append(Paragraph(
        '<font name="Helvetica-Bold">Leitura estatística, não preditiva:</font> classificação de frequência, '
        "sequências e atraso descrevem o comportamento passado das dezenas — nenhum desses indicadores altera "
        "a probabilidade real de uma dezena sair no próximo concurso. Use como material de apoio para "
        "estudar a composição do jogo, não como previsão.",
        nota_style,
    ))

    if sugestoes:
        elementos.append(Paragraph("3. Sugestões de apostas — recomendação combinada", secao_style))
        elementos.append(Paragraph(
            "Combinando os critérios já validados no sistema — paridade equilibrada, meta de repetidas em "
            f"relação ao concurso #{numero} e as dezenas com sinal mais forte de \"quente\" nos sorteios "
            "recentes — seguem sugestões de apostas para servir de ponto de partida na montagem do seu jogo "
            "manual. Cada sugestão prioriza as dezenas em chama e classificadas como quentes, dentro de uma "
            "meta diferente de repetidas e da paridade validada estatisticamente para o projeto.",
            corpo_style,
        ))
        elementos.append(Spacer(1, 6))
        elementos.append(_tabela_sugestoes(sugestoes))
        elementos.append(Spacer(1, 8))
        elementos.append(Paragraph(
            '<font name="Helvetica-Bold">Recomendação, não garantia:</font> estas sugestões combinam critérios '
            "estatísticos já validados no projeto (paridade, repetidas e frequência recente) para orientar a "
            "composição do jogo — elas não aumentam a probabilidade real de acerto, que é a mesma para "
            "qualquer combinação de 15 dezenas. Use como ponto de partida para o seu próprio jogo manual, "
            "ajustando à vontade.",
            nota_style,
        ))

    doc.build(elementos)
    return buffer.getvalue()
