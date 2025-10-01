# ------------------------------ IMPORTS ------------------------------
import os
import logging
import traceback
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# ------------------------------ CONFIGURATION ------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"  # Default to PostgreSQL

if not DATABASE_URL and not USE_SQLITE:
    # Default to PostgreSQL if no environment variables are set
    DATABASE_URL = "postgresql://ibtesamnaeem@localhost:5432/turolytics"

SQLITE_URL = "sqlite:///./turolytics.db"

# ------------------------------ ENGINE CONFIGURATION ------------------------------

def get_database_url() -> str:
    """Get the appropriate database URL based on environment."""
    if USE_SQLITE:
        logger.info("Using SQLite database for development")
        return SQLITE_URL
    else:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")
        logger.info("Using PostgreSQL database")
        return DATABASE_URL

def create_database_engine() -> Engine:
    """Create and configure the database engine."""
    database_url = get_database_url()
    
    if USE_SQLITE:
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  
        )
    else:
        engine = create_engine(
            database_url,
            echo=False,  
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
    
    return engine

# ------------------------------ SESSION CONFIGURATION ------------------------------
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------ DATABASE UTILITIES ------------------------------

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables.
    
    Raises:
        SQLAlchemyError: If table creation fails.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        logger.debug(traceback.format_exc())
        raise

def drop_tables():
    """Drop all database tables.
    
    Raises:
        SQLAlchemyError: If table dropping fails.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error dropping database tables: {e}")
        logger.debug(traceback.format_exc())
        raise


def reset_database():
    """Drop and recreate all tables (useful for testing)."""
    try:
        drop_tables()
        create_tables()
        logger.info("Database reset successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error resetting database: {e}")
        raise


def seed_test_data():
    """Seed database with test data for development."""
    from .models import Account, Vehicle, Trip, TripStatus, VehicleStatus
    
    try:
        db = SessionLocal()
        
        # Create test account
        test_account = Account(
            turo_email="test@example.com",
            account_name="Test User"
        )
        db.add(test_account)
        db.flush()
        
        # Create test vehicle
        test_vehicle = Vehicle(
            account_id=test_account.id,
            turo_vehicle_id="test_vehicle_123",
            name="Test Car 2023",
            status=VehicleStatus.LISTED,
            year=2023,
            make="Test",
            model="Car"
        )
        db.add(test_vehicle)
        db.flush()
        
        # Create test trip
        test_trip = Trip(
            account_id=test_account.id,
            vehicle_id=test_vehicle.id,
            turo_trip_id="test_trip_123",
            status=TripStatus.COMPLETED,
            customer_name="Test Customer",
            price_total=100.0,
            earnings=80.0
        )
        db.add(test_trip)
        
        db.commit()
        logger.info("Test data seeded successfully")
        
    except Exception as e:
        logger.error(f"Error seeding test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# ------------------------------ END OF FILE ------------------------------