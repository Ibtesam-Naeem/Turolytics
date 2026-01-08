#!/usr/bin/env python3
"""
Migration script to remove 'scraped_at' columns from turo_vehicles and turo_reviews tables.
These columns are redundant since updated_at serves the same purpose.
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


def remove_scraped_at_columns():
    """Remove 'scraped_at' columns from turo_vehicles and turo_reviews tables if they exist."""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Process turo_vehicles table
        logger.info("Checking turo_vehicles table...")
        vehicles_columns = inspector.get_columns('turo_vehicles')
        vehicles_column_names = [col['name'] for col in vehicles_columns]
        
        if 'scraped_at' in vehicles_column_names:
            logger.info("Removing 'scraped_at' column from turo_vehicles table...")
            db.execute(text("ALTER TABLE turo_vehicles DROP COLUMN scraped_at"))
            db.commit()
            logger.info("✓ Successfully removed 'scraped_at' column from turo_vehicles table")
        else:
            logger.info("✓ Column 'scraped_at' does not exist in turo_vehicles table")
        
        # Process turo_reviews table
        logger.info("Checking turo_reviews table...")
        reviews_columns = inspector.get_columns('turo_reviews')
        reviews_column_names = [col['name'] for col in reviews_columns]
        
        if 'scraped_at' in reviews_column_names:
            logger.info("Removing 'scraped_at' column from turo_reviews table...")
            db.execute(text("ALTER TABLE turo_reviews DROP COLUMN scraped_at"))
            db.commit()
            logger.info("✓ Successfully removed 'scraped_at' column from turo_reviews table")
        else:
            logger.info("✓ Column 'scraped_at' does not exist in turo_reviews table")
        
        logger.info("\n✓ Migration complete!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error removing columns: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        remove_scraped_at_columns()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
