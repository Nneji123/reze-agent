"""Database session management for Reze AI Agent.

This module provides SQLAlchemy async engine and session management
for storing chat conversations and related data using SQLite/PostgreSQL.
"""

from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.database.base import Base


def create_engine(echo: bool | None = None) -> AsyncEngine:
    """Create the global async SQLAlchemy engine.

    Args:
        echo: Enable SQLAlchemy query logging (overrides config if provided)

    Returns:
        Configured AsyncEngine instance
    """
    database_url = settings.database_url
    echo_setting = echo if echo is not None else settings.database_echo

    engine = create_async_engine(
        database_url,
        echo=echo_setting,
        future=True,
    )
    logger.info(f"SQLAlchemy engine created: {database_url}")
    return engine


# Global async engine and session factory
engine: AsyncEngine = create_engine()

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session; useful for dependency injection.

    This context manager is used throughout the application to handle
    database transactions. The session is automatically closed after use.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """Create all database tables defined in ORM models.

    This is typically called at application startup to ensure the
    database schema exists. It is safe to call multiple times.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Database schema created successfully")
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        raise


async def close_engine() -> None:
    """Close the database engine.

    This should be called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database engine closed")
    except Exception as e:
        logger.error(f"Failed to close database engine: {e}")
