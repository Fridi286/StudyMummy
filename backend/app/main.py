"""
StudyMummy FastAPI Application Entry Point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.middleware.logging_middleware import LoggingMiddleware

# Tools beim Import registrieren
import app.tools.study_tools  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    log = get_logger(__name__)
    log.info(f"StudyMummy API v{settings.app_version} starting [{settings.app_env}]")
    yield
    log.info("StudyMummy API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "StudyMummy – Agentic AI Learning Platform API\n\n"
            "Übungsblatt 03 (HAW Hamburg, WP Agentic AI, SS 2026)\n"
            "Implementiert: LLM-Anbindung, Tool Use & RAG-Grundgerüst."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    import os
    os.makedirs("static/avatars", exist_ok=True)
    
    class CachedStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            response = await super().get_response(path, scope)
            if response.status_code == 200:
                # Cache for 1 year
                response.headers["Cache-Control"] = "public, max-age=31536000"
            return response

    app.mount("/static", CachedStaticFiles(directory="static"), name="static")

    # Middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_dev else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routen
    app.include_router(api_router)

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
