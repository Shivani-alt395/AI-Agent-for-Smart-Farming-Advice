"""
FastAPI application factory and startup logic.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from loguru import logger

from app.api.routes import router
from app.core.config import get_settings
from app.core.rag_pipeline import get_rag_pipeline
from app.services.knowledge_base import load_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize RAG pipeline and load knowledge base on startup
    try:
        rag = get_rag_pipeline()
        if not rag.is_ready:
            logger.info("Vector store empty — loading knowledge base...")
            count = load_knowledge_base()
            logger.info(f"Knowledge base ready: {count} chunks loaded.")
        else:
            logger.info("Knowledge base already loaded in ChromaDB.")
    except Exception as exc:
        logger.warning(f"Knowledge base initialization failed (non-fatal): {exc}")

    logger.info("Smart Farming AI Agent is ready!")
    yield
    logger.info("Shutting down Smart Farming AI Agent.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI Agent for Smart Farming Advice powered by IBM Granite (watsonx.ai). "
            "Provides real-time weather, mandi prices, crop recommendations, pest management, "
            "and soil health guidance in multiple Indian languages."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(router, prefix="/api/v1", tags=["Smart Farming Agent"])

    # Serve frontend static files
    try:
        app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    except Exception:
        pass  # Static directory may not exist in minimal setups

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_frontend():
        """Serve the main frontend HTML."""
        try:
            with open("frontend/index.html", "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(
                content="<h1>Smart Farming AI Agent</h1><p>Visit <a href='/api/docs'>/api/docs</a></p>"
            )

    return app
