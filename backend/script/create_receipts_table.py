#!/usr/bin/env python3
"""
Migration script to create turo_receipts table.
This script creates the receipts table if it doesn't exist.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database.connection import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_receipts_table():
    """Create turo_receipts table if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if table already exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'turo_receipts' in tables:
            logger.info("✓ Table 'turo_receipts' already exists")
            return
        
        logger.info("Creating 'turo_receipts' table...")
        
        # Determine the appropriate JSON type based on the database URL
        db_url = str(engine.url)
        if db_url.startswith("postgresql"):
            json_type = "JSONB"
        elif db_url.startswith("mysql"):
            json_type = "JSON"
        else:  # Default for SQLite and others
            json_type = "TEXT"  # SQLite stores JSON as TEXT
        
        # Create the table
        db.execute(text(f"""
            CREATE TABLE turo_receipts (
                id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
                trip_id INTEGER NOT NULL REFERENCES turo_trips(id) ON DELETE CASCADE,
                reservation_id VARCHAR,
                host_name VARCHAR,
                vehicle_name VARCHAR,
                vehicle_year VARCHAR,
                booked_date VARCHAR,
                trip_start VARCHAR,
                trip_end VARCHAR,
                pickup_location VARCHAR,
                return_location VARCHAR,
                guest_name VARCHAR,
                guest_id VARCHAR,
                distance_included INTEGER,
                kilometers_driven INTEGER,
                overage_rate FLOAT,
                trip_price FLOAT,
                delivery_fee FLOAT,
                trip_total FLOAT,
                turo_fees FLOAT,
                sales_tax FLOAT,
                you_earned FLOAT,
                cost_details {json_type},
                earnings_breakdown {json_type},
                scraped_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes
        db.execute(text("""
            CREATE INDEX idx_receipt_trip ON turo_receipts(trip_id)
        """))
        
        db.execute(text("""
            CREATE INDEX idx_receipt_account ON turo_receipts(account_id)
        """))
        
        db.execute(text("""
            CREATE INDEX idx_receipt_reservation ON turo_receipts(reservation_id)
        """))
        
        db.commit()
        logger.info(f"✓ Successfully created 'turo_receipts' table with {json_type} columns")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error creating table: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_receipts_table()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
