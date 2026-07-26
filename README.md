# Sistema Lotofácil com IA


Aplicação web full-stack para análise e geração de apostas da Lotofácil utilizando Inteligência Artificial (Anthropic Claude).

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy · Alembic |
| Banco de dados | PostgreSQL 15+ |
| Frontend | React 18 · Vite · Tailwind CSS |
| IA | Anthropic Claude (claude-sonnet-4-6) |

## Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 15 ou superior
- Node.js 18 ou superior

## Configuração rápida

### 1. Variáveis de ambiente

Edite o arquivo `.env` na raiz do projeto:

```
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/lotofacil
ANTHROPIC_API_KEY=sua-chave-anthropic
FRONTEND_URL=http://localhost:5173
SECRET_KEY=chave-secreta-forte
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r ../requirements.txt

# Rodar migrations
alembic upgrade head

# Iniciar servidor
uvicorn main:app --reload
```

O servidor sobe em http://localhost:8000
Documentação automática: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend sobe em http://localhost:5173

## Estrutura

```
backend/
  main.py          # Entrypoint FastAPI + CORS + routers
  database.py      # Conexão SQLAlchemy + get_db
  models.py        # Modelos ORM (Sorteio, Aposta, JogoRealizado)
  schemas.py       # Schemas Pydantic
  scheduler.py     # APScheduler (atualização automática de sorteios)
  routers/
    sorteios.py    # CRUD de sorteios
    apostas.py     # CRUD de apostas
    jogos.py       # Registro de jogos realizados
  services/        # Lógica de negócio (Fase 2+)
  alembic/         # Migrations

frontend/
  src/
    pages/         # Dashboard, Sorteios, Apostas, GerarIA
    components/    # Layout (navbar + footer)
    services/      # api.js (axios)
```

## Banco de dados

### Tabela `sorteios`
Armazena resultados oficiais dos concursos da Lotofácil.

### Tabela `apostas`
Apostas cadastradas manualmente ou geradas pela IA.

### Tabela `jogos_realizados`
Conferência entre apostas e resultados (acertos, premiações).
