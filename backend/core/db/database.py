# ------------------------------ IMPORTS ------------------------------
import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .base import Base
from ..config.settings import settings

# ------------------------------ DATABASE CONFIGURATION ------------------------------

def get_database_url() -> str:
    """Get the PostgreSQL database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql://user:password@localhost:5432/dbname"
        )
    return database_url

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=False  
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------ SESSION MANAGEMENT ------------------------------

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit/rollback.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_db_session() as db:
            account = db.query(Account).first()
            db.commit()
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

def create_tables():
    """Create all database tables in PostgreSQL."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)

def test_connection():
    """Test the database connection."""
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------ END OF FILE ------------------------------