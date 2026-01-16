"""Reze AI Agent - FastAPI Application.

This is the main FastAPI application for Reze, a chat-only AI agent
for Resend.com powered by GLM 4.7 from z.ai.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.api.routers.chat_router import router as chat_router
from src.config import settings
from src.database.session import init_db
from src.services.memvid import memvid


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    logger.info("Starting Reze AI Agent application...")

    try:
        # Initialize database schema
        logger.info("Initializing database schema...")
        await init_db()
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")

    try:
        # Initialize Memvid service (for RAG)
        logger.info("Initializing Memvid service...")
        stats = await memvid.get_stats()
        logger.info(f"Memvid service initialized: {stats}")
    except Exception as e:
        logger.error(f"Failed to initialize Memvid service: {e}")

    yield
    logger.info("Shutting down Reze AI Agent application...")


app = FastAPI(
    title="Reze AI Agent",
    description="Chat-based AI agent for Resend.com with GLM 4.7 and Memvid RAG",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "reze-ai-agent",
        "version": "0.1.0",
    }


# Include routers
app.include_router(chat_router)

# Mount static files directory
from pathlib import Path

static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve index.html at root path
@app.get("/")
async def serve_chat_interface():
    """Serve chat interface HTML page."""
    index_file = Path(__file__).parent.parent / "static" / "index.html"
    if index_file.exists():
        from fastapi.responses import FileResponse

        return FileResponse(index_file)
    return {
        "message": "Chat interface not found. Please ensure static/index.html exists."
    }
