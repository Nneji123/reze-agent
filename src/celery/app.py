"""Celery application configuration."""

from loguru import logger

from celery import Celery
from src.config import settings

# Configure logging

# Create Celery app
celery = Celery(__name__)

# Celery configuration
celery.conf.update(
    # Task settings
    broker_url=settings.celery.celery_broker_url,
    backend=settings.celery.celery_result_backend,
    beat_schedule={},
)

logger.info("Celery app configured successfully")
