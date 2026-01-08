#!/usr/bin/env python3
"""
Migration script to add utilization_goal column to turo_vehicles table.
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


def add_utilization_goal_column():
    """Add utilization_goal column to turo_vehicles table if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if column already exists
        inspector = inspect(engine)
        columns = inspector.get_columns('turo_vehicles')
        column_names = [col['name'] for col in columns]
        
        if 'utilization_goal' in column_names:
            logger.info("✓ Column 'utilization_goal' already exists in turo_vehicles table")
            return
        
        logger.info("Adding 'utilization_goal' column to turo_vehicles table...")
        
        # Add the column
        db.execute(text("""
            ALTER TABLE turo_vehicles 
            ADD COLUMN utilization_goal DOUBLE PRECISION NULL
        """))
        
        db.commit()
        logger.info("✓ Successfully added 'utilization_goal' column to turo_vehicles table")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error adding column: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        add_utilization_goal_column()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
