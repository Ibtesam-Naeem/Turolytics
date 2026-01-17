#!/usr/bin/env python3
"""
Migration script to add optional columns to waitlist table.
Adds: vehicle_count, tracking_product, tracking_product_other, would_use, price_willing, feedback
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


def add_waitlist_columns():
    """Add optional columns to waitlist table if they don't exist."""
    db = SessionLocal()
    try:
        # Check if table exists
        inspector = inspect(engine)
        if 'waitlist' not in inspector.get_table_names():
            logger.error("✗ Table 'waitlist' does not exist. Please create it first.")
            return
        
        # Get existing columns
        columns = inspector.get_columns('waitlist')
        column_names = [col['name'] for col in columns]
        
        # Columns to add
        columns_to_add = [
            ('vehicle_count', 'VARCHAR NULL'),
            ('tracking_product', 'VARCHAR NULL'),
            ('tracking_product_other', 'VARCHAR NULL'),
            ('would_use', 'VARCHAR NULL'),
            ('price_willing', 'VARCHAR NULL'),
            ('feedback', 'TEXT NULL'),
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name in column_names:
                logger.info(f"✓ Column '{column_name}' already exists in waitlist table")
            else:
                logger.info(f"Adding column '{column_name}' to waitlist table...")
                db.execute(text(f"""
                    ALTER TABLE waitlist 
                    ADD COLUMN {column_name} {column_type}
                """))
                db.commit()
                logger.info(f"✓ Successfully added '{column_name}' column to waitlist table")
        
        logger.info("✓ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error adding columns: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        add_waitlist_columns()
        logger.info("✓ Script completed successfully")
    except Exception as e:
        logger.error(f"✗ Script failed: {e}")
        sys.exit(1)
