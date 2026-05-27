# DataAtlas

AI-powered enterprise data catalog. Discover, understand, and govern your data.

## Architecture

```
backend/                  Python 3.11 / FastAPI
├── app/core/             Config, structured logging (structlog), exceptions
├── app/domain/schemas/   Pydantic v2 I/O contracts (no DB dependency)
├── app/persistence/      SQLAlchemy 2.0 async ORM + Alembic migrations
├── app/ingestion/        Database connectors (PostgreSQL; extensible)
├── app/metadata/         Schema extractor + deterministic PII detection
├── app/lineage/          sqlglot SQL parser + networkx graph engine
├── app/ai/               Provider abstraction: OpenAI / Anthropic / Ollama
├── app/services/         Orchestration: catalog, lineage, impact, AI, ingestion
└── app/api/v1/           FastAPI REST endpoints

frontend/                 Next.js 15 / TypeScript / Tailwind / React Flow
├── src/app/              App router pages
├── src/components/       UI: tables, lineage graph, layout
└── src/lib/api/          Typed API client + type definitions
```

## Quick Start

### 1. Start infrastructure

```bash
cp .env.example .env
# Add your AI provider key to .env

docker compose up postgres -d
```

### 2. Backend

```bash
cd backend
pip install -e ".[dev]"
cp .env.example .env        # configure DATABASE_URL and AI keys

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# App at http://localhost:3000
```

### 4. Full stack with Docker

```bash
docker compose up --build
```

## Ingest a Database

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/scan \
  -H "Content-Type: application/json" \
  -d '{
    "db_url": "postgresql://user:pass@host:5432/mydb",
    "infer_view_lineage": true
  }'
```

## AI Enrichment

```bash
# Enrich a table (generates description, business purpose, column docs)
curl -X POST "http://localhost:8000/api/v1/ingestion/enrich/<table-id>"
```

## AI Providers

Set `AI_PROVIDER` in `.env`:

| Provider | Environment Variables |
|---|---|
| `openai` | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `anthropic` | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |
| `ollama` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/tables` | List tables (paginated, filterable) |
| GET | `/api/v1/tables/search?q=...` | Full-text search |
| GET | `/api/v1/tables/:id` | Table detail with AI docs |
| PATCH | `/api/v1/tables/:id` | Update description/tags/owner |
| GET | `/api/v1/tables/:id/columns` | Column list |
| GET | `/api/v1/lineage/:id` | Lineage graph (nodes + edges) |
| POST | `/api/v1/lineage/edges` | Manually add a lineage edge |
| GET | `/api/v1/impact/:id` | Blast-radius analysis |
| POST | `/api/v1/ingestion/scan` | Trigger schema scan |
| POST | `/api/v1/ingestion/enrich/:id` | Trigger AI enrichment |
| GET | `/health` | Health check |

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Stack

**Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, Pydantic v2,
sqlglot, networkx, structlog, tenacity, httpx

**Frontend**: Next.js 15, TypeScript, Tailwind CSS, React Flow (@xyflow/react),
TanStack Query, Axios

**Database**: PostgreSQL 16

**AI**: OpenAI, Anthropic, Ollama (pluggable via provider abstraction)
