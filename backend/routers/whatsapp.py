import re
from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
import anthropic
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Sorteio

router = APIRouter()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _extrair_numero_concurso(mensagem: str) -> int | None:
    """Detecta se a mensagem pergunta sobre um concurso específico, tipo
    'resultado do concurso 3700' ou 'o que saiu no 3700'."""
    match = re.search(r"\b(\d{3,4})\b", mensagem)
    if match:
        numero = int(match.group(1))
        if 1 <= numero <= 9999:
            return numero
    return None


def get_contexto_banco(mensagem: str):
    db = SessionLocal()
    try:
        total = db.query(Sorteio).count()
        ultimo = db.query(Sorteio).order_by(Sorteio.numero_concurso.desc()).first()
        recentes = db.query(Sorteio).order_by(Sorteio.numero_concurso.desc()).limit(10).all()

        if not ultimo:
            return "Banco de dados sem sorteios cadastrados ainda."

        frequencia = {}
        for s in recentes:
            for d in s.dezenas:
                frequencia[d] = frequencia.get(d, 0) + 1

        mais_quentes = sorted(frequencia.items(), key=lambda x: x[1], reverse=True)[:8]
        mais_frias = sorted(frequencia.items(), key=lambda x: x[1])[:8]

        contexto = f"""DADOS REAIS DO BANCO DE DADOS:
- Total de sorteios cadastrados: {total}
- Último sorteio: #{ultimo.numero_concurso} em {ultimo.data_sorteio}
- Dezenas do último sorteio: {sorted(ultimo.dezenas)}
- Dezenas mais quentes (últimos 10 sorteios): {[d for d,f in mais_quentes]}
- Dezenas mais frias (últimos 10 sorteios): {[d for d,f in mais_frias]}
"""

        # Se a mensagem menciona um número de concurso específico, busca ele direto no banco
        numero_perguntado = _extrair_numero_concurso(mensagem)
        if numero_perguntado:
            sorteio_especifico = (
                db.query(Sorteio)
                .filter(Sorteio.numero_concurso == numero_perguntado)
                .first()
            )
            if sorteio_especifico:
                contexto += f"""
DADO ESPECÍFICO SOLICITADO — Concurso #{sorteio_especifico.numero_concurso}:
- Data: {sorteio_especifico.data_sorteio}
- Dezenas sorteadas: {sorted(sorteio_especifico.dezenas)}
- Pares: {sorteio_especifico.total_pares} / Ímpares: {sorteio_especifico.total_impares}
- Repetidas em relação ao concurso anterior: {sorteio_especifico.repetidas_anterior}
"""
            else:
                contexto += f"""
DADO ESPECÍFICO SOLICITADO — Concurso #{numero_perguntado}: NÃO ENCONTRADO na nossa base local.
(Nossa base cobre do concurso #1 até o #{ultimo.numero_concurso}. Se o número pedido estiver fora
desse intervalo, avise educadamente que ainda não temos esse concurso registrado — não invente
o resultado.)
"""

        return contexto
    except Exception as e:
        return f"Erro ao consultar banco: {str(e)}"
    finally:
        db.close()


SYSTEM_PROMPT = """Você é o LotoSorte 🍀, assistente pessoal do Sérgio para análise da Lotofácil.

Sua personalidade:
- Animado, amigável e motivador
- Usa emojis 🍀🎯🎲 com naturalidade
- Sempre termina as mensagens com "Boa sorte, Sérgio! 🍀"
- Respostas curtas e diretas (máximo 3 parágrafos)
- Conhece profundamente estatísticas da Lotofácil

REGRA CRÍTICA SOBRE A BASE DE DADOS:
Você tem acesso aos dados REAIS e OFICIAIS do banco de dados do sistema Lotofácil IA do Sérgio,
que contém o histórico completo de sorteios. Essa base é a fonte de verdade — trate-a como tal.

NUNCA, em nenhuma hipótese, oriente o Sérgio a consultar o site da Caixa Econômica Federal ou
qualquer fonte externa para saber resultados de sorteios. Se o concurso perguntado estiver
presente no contexto fornecido, responda com os dados dele diretamente. Se não estiver
disponível no contexto (fora do intervalo que a base cobre), diga isso claramente e sugira que
ele rode a atualização da base no sistema — nunca mande ele procurar em outro lugar.

Responda sempre em português brasileiro."""


@router.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
):
    mensagem = Body.strip()
    contexto = get_contexto_banco(mensagem)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"{contexto}\n\nPergunta do Sérgio: {mensagem}"}
            ]
        )
        resposta = response.content[0].text

    except Exception as e:
        resposta = "Ops! Tive um probleminha técnico 😅 Tente novamente! Boa sorte, Sérgio! 🍀"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{resposta}</Message>
</Response>"""

    return PlainTextResponse(content=twiml, media_type="application/xml")
