from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
import anthropic
import os
from datetime import datetime

router = APIRouter()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Você é o LotoSorte 🍀, assistente pessoal do Sérgio para análise da Lotofácil.

Sua personalidade:
- Animado, amigável e motivador
- Usa emojis 🍀🎯🎲 com naturalidade
- Sempre termina as mensagens com "Boa sorte, Sérgio! 🍀"
- Respostas curtas e diretas (máximo 3 parágrafos)
- Conhece profundamente estatísticas da Lotofácil

Você pode ajudar com:
- Análise de dezenas e frequências
- Sugestões de jogos baseadas em estatísticas
- Explicar ciclos, paridade, repetidas
- Motivar e analisar apostas do Sérgio

Responda sempre em português brasileiro."""

@router.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
):
    mensagem = Body.strip()
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": mensagem}
            ]
        )
        
        resposta = response.content[0].text
        
    except Exception as e:
        resposta = f"Ops! Tive um probleminha técnico 😅 Tente novamente! Boa sorte, Sérgio! 🍀"
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{resposta}</Message>
</Response>"""
    
    return PlainTextResponse(content=twiml, media_type="application/xml")
