"""Reze AI Agent - Main entry point.

This is a chat-only AI agent for Resend.com that uses:
- GLM 4.7 from z.ai for intelligence
- Memvid for RAG (Retrieval-Augmented Generation)
- Resend.com API for email operations
- Native FastAPI streaming for real-time responses
"""

import uvicorn
from loguru import logger

from src.config import settings


def main() -> None:
    """Run the Reze AI Agent FastAPI application."""
    logger.info("=" * 80)
    logger.info("🚀 Reze AI Agent Starting...")
    logger.info("=" * 80)
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"GLM Model: {settings.glm_model}")
    logger.info(f"Memvid File: {settings.memvid_file_path}")
    logger.info(f"Database: {settings.database_url}")
    logger.info("=" * 80)

    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
