"""Logging configuration."""

import sys
from loguru import logger
from config.config import settings


def setup_logger():
    """Configure the application logger."""

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
               "<level>{message}</level>",
        level=settings.log_level
    )

    # Add file handler
    logger.add(
        "logs/content_creator_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",
        compression="zip",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
               "{name}:{function} - {message}"
    )

    logger.info("Logger initialized")
