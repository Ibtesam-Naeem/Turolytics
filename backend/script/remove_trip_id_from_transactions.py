#!/usr/bin/env python3
"""
Migration script to remove 'trip_id' column from turo_transactions table.
Transactions can be linked to trips via reservation_id instead.
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


def remove_trip_id_column():
    """Remove 'trip_id' column from turo_transactions table if it exists."""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if 'turo_transactions' not in inspector.get_table_names():
            logger.warning("Table 'turo_transactions' does not exist. Skipping migration.")
            return
        
        # Get columns
        logger.info("Checking turo_transactions table...")
        columns = inspector.get_columns('turo_transactions')
        column_names = [col['name'] for col in columns]
        
        if 'trip_id' in column_names:
            logger.info("Removing 'trip_id' column from turo_transactions table...")
            
            # Check if there's a foreign key constraint
            foreign_keys = inspector.get_foreign_keys('turo_transactions')
            fk_to_drop = None
            for fk in foreign_keys:
                if 'trip_id' in fk.get('constrained_columns', []):
                    fk_to_drop = fk['name']
                    break
            
            # Drop foreign key constraint if it exists
            if fk_to_drop:
                logger.info(f"Dropping foreign key constraint '{fk_to_drop}'...")
                db.execute(text(f"ALTER TABLE turo_transactions DROP CONSTRAINT IF EXISTS {fk_to_drop}"))
                db.commit()
            
            # Drop the column
            db.execute(text("ALTER TABLE turo_transactions DROP COLUMN IF EXISTS trip_id"))
            db.commit()
            logger.info("✓ Successfully removed 'trip_id' column from turo_transactions table")
        else:
            logger.info("✓ Column 'trip_id' does not exist in turo_transactions table (may have already been removed)")
        
        # Check if there's an index on trip_id that needs to be dropped
        indexes = inspector.get_indexes('turo_transactions')
        for index in indexes:
            if 'trip_id' in index.get('column_names', []):
                index_name = index['name']
                logger.info(f"Dropping index '{index_name}' on trip_id...")
                db.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                db.commit()
                logger.info(f"✓ Dropped index '{index_name}'")
        
        logger.info("\n✓ Migration complete!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error removing column: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        remove_trip_id_column()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
