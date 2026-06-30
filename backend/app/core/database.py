"""Database configuration and session management.

This module initializes the SQLAlchemy database engine and provides a dependency
for retrieving database sessions.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

import logging
from sqlalchemy.exc import OperationalError

logger = logging.getLogger("uvicorn.error")

# Try to connect to PostgreSQL, fallback to SQLite if connection fails
try:
    if settings.sqlalchemy_database_uri.startswith("sqlite"):
        engine = create_engine(
            settings.sqlalchemy_database_uri, connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            settings.sqlalchemy_database_uri, pool_pre_ping=True
        )
    # Test connection
    with engine.connect() as conn:
        pass
except OperationalError:
    logger.warning("Could not connect to PostgreSQL server. Falling back to local SQLite: interviewpilot.db")
    engine = create_engine(
        "sqlite:///./interviewpilot.db", connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Dependency generator that provides a database session and closes it on completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
