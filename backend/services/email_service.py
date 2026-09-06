"""
Envio de e-mail de aviso da conferência automática — via Gmail (SMTP + App
Password), sem depender de nenhum serviço pago.

Variáveis de ambiente necessárias (ver README/checklist de configuração):
  GMAIL_USER          endereço Gmail que vai ENVIAR o aviso
  GMAIL_APP_PASSWORD  senha de app gerada em myaccount.google.com/apppasswords
                       (não é a senha normal da conta — é preciso ter a
                       verificação em duas etapas ativada para gerar uma)
  EMAIL_DESTINO        endereço que vai RECEBER o aviso (pode ser o mesmo
                       GMAIL_USER, ou outro e-mail do Sérgio)

Se qualquer uma dessas variáveis não estiver configurada, a função apenas
registra um aviso no log e não faz nada — nunca derruba a aplicação por
causa disso.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.conferencia import ResultadoConferencia

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _montar_corpo(resultados: "list[ResultadoConferencia]") -> str:
    linhas = []
    premiadas = [r for r in resultados if r.premiado]

    if premiadas:
        linhas.append(f"🎉 {len(premiadas)} aposta(s) premiada(s) nesta conferência!\n")

    for r in resultados:
        status = f"PREMIADO — {r.faixa_premio}" if r.premiado else "sem prêmio"
        linhas.append(
            f"- {r.nome_aposta} (concurso {r.numero_concurso}): "
            f"{r.total_acertos} acertos [{status}]\n"
            f"  Apostado:  {r.dezenas_apostadas}\n"
            f"  Sorteado:  {r.dezenas_sorteadas}\n"
            f"  Acertos:   {r.dezenas_acertadas}\n"
        )

    linhas.append("\n— Conferência automática do Sistema Lotofácil, sem precisar lembrar de checar. 🍀")
    return "\n".join(linhas)


def enviar_email_conferencia(resultados: "list[ResultadoConferencia]") -> bool:
    """Retorna True se o e-mail foi enviado, False se pulou por falta de configuração."""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    email_destino = os.getenv("EMAIL_DESTINO", gmail_user)

    if not gmail_user or not gmail_app_password or not email_destino:
        logger.warning(
            "Notificação por e-mail não configurada (GMAIL_USER/GMAIL_APP_PASSWORD/EMAIL_DESTINO "
            "ausentes) — conferência foi salva no banco, mas nenhum aviso foi enviado."
        )
        return False

    premiadas = sum(1 for r in resultados if r.premiado)
    assunto = (
        f"🍀 Lotofácil: {len(resultados)} aposta(s) conferida(s)"
        + (f" — {premiadas} premiada(s)!" if premiadas else "")
    )

    msg = MIMEText(_montar_corpo(resultados), "plain", "utf-8")
    msg["Subject"] = assunto
    msg["From"] = gmail_user
    msg["To"] = email_destino

    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=contexto) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, [email_destino], msg.as_string())

    logger.info("E-mail de conferência enviado para %s (%d aposta(s)).", email_destino, len(resultados))
    return True
