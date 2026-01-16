"""Test suite for Reze AI Agent.

This module sets up the test configuration and exports
common test fixtures for testing the AI agent, Resend API,
Memvid RAG system, and conversation management.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from loguru import logger

# Configure logging for tests
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <level>{name}</level>{message}",
    level="DEBUG",
)

# Test configuration
pytest_plugins = ["pytest-asyncio"]


# Common test fixtures
@pytest.fixture(scope="session")
def anyio_backend():
    """Configure pytest-asyncio for FastAPI async tests."""
    return "asyncio"


@pytest.fixture
def event_loop_policy(anyio_backend):
    """Event loop policy for async tests."""
    return anyio_backend


@pytest.fixture
async def mock_env_vars():
    """Mock environment variables for tests."""
    import os

    os.environ.setdefault("GLM_API_KEY", "test_glm_api_key")
    os.environ.setdefault("GLM_BASE_URL", "https://test.open.bigmodel.cn/api/paas/v4")
    os.environ.setdefault("GLM_MODEL", "glm-4.7")
    os.environ.setdefault("RESEND_API_KEY", "re_test_api_key")
    os.environ.setdefault("RESEND_FROM_EMAIL", "test@resend.com")
    os.environ.setdefault("RESEND_BASE_URL", "https://api.resend.com")
    os.environ.setdefault("MEMVID_FILE_PATH", "./test_memvid.mv2")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    os.environ.setdefault("DEBUG", "False")
    os.environ.setdefault("LOG_LEVEL", "WARNING")

    yield

    # Cleanup after tests
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    if os.path.exists("./test_memvid.mv2"):
        os.remove("./test_memvid.mv2")


@pytest.fixture
async def clean_test_db():
    """Clean test database before/after tests."""
    # Create tables
    from src.database.base import Base
    from src.database.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


__all__ = [
    "anyio_backend",
    "event_loop_policy",
    "mock_env_vars",
    "clean_test_db",
]
