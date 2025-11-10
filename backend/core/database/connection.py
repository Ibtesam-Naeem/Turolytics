# ------------------------------ IMPORTS ------------------------------
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import logging

from core.config.settings import settings

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ BASE CLASS ------------------------------
Base = declarative_base()

# ------------------------------ DATABASE ENGINE ------------------------------
engine = create_engine(
    settings.database.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# ------------------------------ SESSION FACTORY ------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------ DATABASE FUNCTIONS ------------------------------

def get_db() -> Generator:
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database - create all tables."""
    try:
        from core.database.models import (
            Account,
            Vehicle,
            Trip,
            Review,
            EarningsBreakdown,
            VehicleEarnings,
            SessionStorage,
        )
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
   
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# ------------------------------ END OF FILE ------------------------------

