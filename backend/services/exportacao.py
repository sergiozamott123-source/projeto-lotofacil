"""
Geração de PDF com a lista de apostas do usuário — pensado para imprimir
ou levar até a lotérica na hora de registrar os jogos.
"""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

ROXO = colors.HexColor("#6d28d9")
ROXO_CLARO = colors.HexColor("#f5f3ff")
CINZA = colors.HexColor("#64748b")
BORDA = colors.HexColor("#e2e8f0")

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
