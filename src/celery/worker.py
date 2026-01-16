"""Celery worker startup script."""

import subprocess
import sys

from loguru import logger

if __name__ == "__main__":
    logger.info("Starting Celery worker...")

    # Use subprocess to run celery worker command
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "src.celery.app:celery",
                "worker",
                "--loglevel=INFO",
                "--concurrency=4",
                "--hostname=timi-worker@%h",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Celery worker failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Celery worker stopped by user")
        sys.exit(0)
