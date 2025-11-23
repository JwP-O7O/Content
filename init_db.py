"""Database initialization script."""

import sys
from loguru import logger

from src.database.connection import init_db, drop_db
from src.utils.logger import setup_logger


def initialize_database(reset: bool = False):
    """
    Initialize the database.

    Args:
        reset: If True, drop all tables before creating them
    """
    setup_logger()

    logger.info("Initializing database...")

    if reset:
        logger.warning("Resetting database (all data will be lost)...")
        response = input("Are you sure? Type 'yes' to confirm: ")

        if response.lower() != "yes":
            logger.info("Database reset cancelled")
            return

        drop_db()
        logger.info("Database reset complete")

    # Create all tables
    init_db()

    logger.info("Database initialized successfully!")
    logger.info("You can now start the Content Creator system")


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    initialize_database(reset=reset)
