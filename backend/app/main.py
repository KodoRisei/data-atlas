from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import DataAtlasError, NotFoundError
from app.core.logging import configure_logging, get_logger
from app.persistence.database import close_engine, get_engine

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    configure_logging()
    settings = get_settings()
    log.info(
        "data_atlas_starting",
        env=settings.app_env,
        ai_provider=settings.ai_provider,
    )
    # Warm up the database connection pool
    get_engine()
    yield
    await close_engine()
    log.info("data_atlas_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="DataAtlas API",
        description="AI-powered enterprise data catalog",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, Any]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "env": settings.app_env,
            "ai_provider": settings.ai_provider,
        }

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "context": exc.context},
        )

    @app.exception_handler(DataAtlasError)
    async def domain_error_handler(
        request: Request, exc: DataAtlasError
    ) -> JSONResponse:
        log.warning("domain_error", error=exc.message, context=exc.context)
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message, "context": exc.context},
        )

    return app


app = create_app()
