from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

from database import engine, Base
from routers import sorteios, apostas, jogos, analise, ia
from scheduler import iniciar_scheduler, parar_scheduler

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_scheduler()
    yield
    parar_scheduler()


app = FastAPI(
    title="Lotofácil API",
    description="API para análise e geração de apostas da Lotofácil com IA",
    version="1.0.0",
    lifespan=lifespan,
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sorteios.router, prefix="/api")
app.include_router(apostas.router, prefix="/api")
app.include_router(jogos.router, prefix="/api")
app.include_router(analise.router, prefix="/api")
app.include_router(ia.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "message": "Lotofácil API rodando"}


@app.get("/health")
def health():
    return {"status": "healthy"}
