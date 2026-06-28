import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from services.scraper import buscar_e_salvar_ultimo_sorteio

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def atualizar_sorteios():
    logger.info("Iniciando atualização automática de sorteios...")
    db = SessionLocal()
    try:
        resultado = buscar_e_salvar_ultimo_sorteio(db)
        logger.info("Resultado: %s", resultado)
    except Exception:
        logger.exception("Falha na atualização automática de sorteios.")
    finally:
        db.close()


def iniciar_scheduler():
    scheduler.add_job(
        atualizar_sorteios,
        trigger=CronTrigger(hour=22, minute=0),
        id="atualizar_sorteios",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado — atualizações diárias às 22h00")


def parar_scheduler():
    scheduler.shutdown()
