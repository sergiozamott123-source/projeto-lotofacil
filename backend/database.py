from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# pool_pre_ping: o Neon (plano gratuito) desliga o banco quando fica ocioso
# e derruba as conexões abertas. Sem isso, a primeira requisição depois de
# um tempo parado falha com "SSL connection has been closed unexpectedly".
# Com o ping, a conexão morta é descartada e trocada por uma nova sozinha.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
