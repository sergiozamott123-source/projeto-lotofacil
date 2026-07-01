from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
import anthropic
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Sorteio

router = APIRouter()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_contexto_banco():
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

Você tem acesso aos dados REAIS do banco de dados do sistema Lotofácil IA do Sérgio.
Use sempre os dados reais fornecidos no contexto para responder com precisão.
Responda sempre em português brasileiro."""

@router.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
):
    mensagem = Body.strip()
    contexto = get_contexto_banco()
    
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
