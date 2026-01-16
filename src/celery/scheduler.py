"""Celery Beat scheduler startup script."""

import subprocess
import sys

from loguru import logger

if __name__ == "__main__":
    logger.info("Starting Celery Beat scheduler...")

    # Use subprocess to run celery beat command
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "src.celery.app:celery",
                "beat",
                "--loglevel=INFO",
                "--schedule=celerybeat-schedule",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Celery Beat failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Celery Beat stopped by user")
        sys.exit(0)
