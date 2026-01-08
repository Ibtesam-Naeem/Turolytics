#!/usr/bin/env python3
"""
Migration script to add listed_on_turo_date column to turo_vehicles table.
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


def add_listed_on_turo_date_column():
    """Add listed_on_turo_date column to turo_vehicles table if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if column already exists
        inspector = inspect(engine)
        columns = inspector.get_columns('turo_vehicles')
        column_names = [col['name'] for col in columns]
        
        if 'listed_on_turo_date' in column_names:
            logger.info("✓ Column 'listed_on_turo_date' already exists in turo_vehicles table")
            return
        
        logger.info("Adding 'listed_on_turo_date' column to turo_vehicles table...")
        
        # Add the column
        db.execute(text("""
            ALTER TABLE turo_vehicles 
            ADD COLUMN listed_on_turo_date TIMESTAMP WITH TIME ZONE NULL
        """))
        
        db.commit()
        logger.info("✓ Successfully added 'listed_on_turo_date' column to turo_vehicles table")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error adding column: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        add_listed_on_turo_date_column()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
