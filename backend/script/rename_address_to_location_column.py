#!/usr/bin/env python3
"""
Migration script to rename 'address' column to 'location' in turo_trips table.
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


def rename_address_to_location_column():
    """Rename 'address' column to 'location' in turo_trips table if it exists."""
    db = SessionLocal()
    try:
        # Check if column exists
        inspector = inspect(engine)
        columns = inspector.get_columns('turo_trips')
        column_names = [col['name'] for col in columns]
        
        if 'address' not in column_names:
            logger.info("✓ Column 'address' does not exist in turo_trips table (may have already been renamed)")
            if 'location' in column_names:
                logger.info("✓ Column 'location' already exists in turo_trips table")
            return
        
        if 'location' in column_names:
            logger.warning("⚠ Column 'location' already exists. Dropping 'address' column instead of renaming.")
            db.execute(text("ALTER TABLE turo_trips DROP COLUMN address"))
            db.commit()
            logger.info("✓ Dropped 'address' column from turo_trips table")
            return
        
        logger.info("Renaming 'address' column to 'location' in turo_trips table...")
        
        # Rename the column
        db.execute(text("""
            ALTER TABLE turo_trips 
            RENAME COLUMN address TO location
        """))
        
        db.commit()
        logger.info("✓ Successfully renamed 'address' column to 'location' in turo_trips table")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error renaming column: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        rename_address_to_location_column()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
