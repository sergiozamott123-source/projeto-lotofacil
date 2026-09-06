import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import SessionLocal
from services.atualizacao import executar_atualizacao_e_conferencia

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def atualizar_sorteios():
    logger.info("Iniciando atualização automática de sorteios...")
    db = SessionLocal()
    try:
        resultado = executar_atualizacao_e_conferencia(db)
        logger.info("Resultado: %s", resultado)
    except Exception:
        logger.exception("Falha na atualização automática de sorteios.")
    finally:
        db.close()

def iniciar_scheduler():
    # NOTA (plano gratuito / Render): este agendador só dispara se o processo
    # estiver de pé no horário exato — e o Render dorme sozinho depois de
    # inatividade. Por isso o gatilho principal passou a ser o GitHub Actions
    # chamando GET /api/sorteios/atualizar de fora (ver .github/workflows/).
    # Este agendador interno continua rodando como reforço, para os casos em
    # que o backend já esteja acordado por outro motivo nesse horário.
    scheduler.add_job(
        atualizar_sorteios,
        trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
        id="atualizar_sorteios_21h",
        replace_existing=True,
    )
    scheduler.add_job(
        atualizar_sorteios,
        trigger=CronTrigger(hour=1, minute=0, timezone="UTC"),
        id="atualizar_sorteios_22h",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado — atualizações às 21h e 22h (Brasília)")

def parar_scheduler():
    scheduler.shutdown()
