# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (from `backend/`)

```bash
pip install -e ".[dev]"          # install with dev dependencies
uvicorn app.main:app --reload    # dev server on :8000
alembic upgrade head             # run migrations
alembic revision --autogenerate -m "description"  # generate migration

pytest tests/ -v                 # run all tests
pytest tests/test_pii_detector.py -v  # run a single test file

ruff check .                     # lint
ruff format .                    # format
mypy app/                        # type-check
```

### Frontend (from `frontend/`)

```bash
npm install
npm run dev          # dev server on :3000
npm run build        # production build
npm run type-check   # tsc --noEmit
npm run lint         # next lint
```

### Infrastructure

```bash
docker compose up postgres -d    # start only the DB
docker compose up --build        # full stack
```

## Architecture

### Backend layers (top → bottom)

```
API routes (app/api/v1/)
  → FastAPI deps (app/api/deps.py)   ← wires services via Depends
  → Services (app/services/)         ← orchestration, business logic
  → Repositories (app/persistence/repositories/)  ← DB queries
  → ORM models (app/persistence/models.py)
```

**Domain schemas** (`app/domain/schemas/`) are pure Pydantic v2 I/O contracts with no SQLAlchemy dependency. All API endpoints return these, not ORM objects.

**Dependency injection** is done entirely in `app/api/deps.py`. Services are instantiated per-request with an injected `AsyncSession`. The `*Dep` type aliases (`CatalogDep`, `LineageDep`, etc.) are the pattern used in route signatures.

**Settings** (`app/core/config.py`): `get_settings()` is `@lru_cache`-cached. The backend reads `backend/.env` (not the root `.env`, which is for Docker).

### AI provider abstraction

`app/ai/base.py` defines `BaseAIProvider`. Three providers implement it: `openai_provider.py`, `anthropic_provider.py`, `ollama_provider.py`. The active provider is selected at runtime by `app/ai/registry.py`'s `get_ai_provider()` (also `@lru_cache`) based on the `AI_PROVIDER` env var. Providers are imported lazily so startup doesn't fail if no API key is set.

Prompts live in `app/ai/prompts.py`.

### Ingestion pipeline

`app/ingestion/base.py` defines `BaseConnector` (abstract async context manager). Add new DB connectors by subclassing it and registering in `app/ingestion/registry.py`. The `IngestionService` orchestrates: connect → scan → `MetadataExtractor.persist()` → auto-detect view lineage via `LineageService`.

PII detection (`app/metadata/pii_detector.py`) is fully deterministic — regex patterns on column names, no AI call needed.

### Lineage

SQL lineage uses **sqlglot** to parse view definitions and INSERT/CREATE AS SELECT. `extract_lineage_from_sql()` returns upstream source tables. `extract_lineage_from_dbt_model()` stubs out dbt macros (`{{ ref() }}`, `{{ source() }}`) before parsing. The in-memory graph for impact analysis uses **networkx** (`app/lineage/graph.py`).

### Frontend

`src/lib/api/client.ts` is the single typed API client (axios). All API calls go through it; never call `fetch` directly in components.

Data fetching uses **TanStack Query** (`@tanstack/react-query`). The lineage graph UI is built with **React Flow** (`@xyflow/react`).

The backend URL is configured via `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

### Error handling

Custom exceptions in `app/core/exceptions.py` map to HTTP status codes in `app/main.py`:
- `NotFoundError` → 404
- `DataAtlasError` (base) → 400

Use `get_logger(__name__)` from `app/core/logging.py` (structlog) for all logging. Log event names use `snake_case` strings as the first argument.
