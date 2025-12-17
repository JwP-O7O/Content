"""Database connection and session management."""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.config import settings
from src.database.models import Base

# Create engine
engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=3600, echo=settings.log_level == "DEBUG"
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def drop_db():
    """Drop all tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with get_db() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session (remember to close it manually).

    Usage:
        db = get_db_session()
        try:
            db.query(Model).all()
        finally:
            db.close()
    """
    return SessionLocal()
