#!/usr/bin/env python3
"""
Migration script to add notified_at column to waitlist table.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database.connection import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_notified_at_column():
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if 'waitlist' not in inspector.get_table_names():
            logger.error("Table 'waitlist' does not exist")
            return
        
        columns = inspector.get_columns('waitlist')
        column_names = [col['name'] for col in columns]
        
        if 'notified_at' in column_names:
            logger.info("✓ Column 'notified_at' already exists")
            return
        
        logger.info("Adding 'notified_at' column...")
        db.execute(text("""
            ALTER TABLE waitlist 
            ADD COLUMN notified_at TIMESTAMP WITH TIME ZONE NULL
        """))
        db.commit()
        logger.info("✓ Successfully added 'notified_at' column")
    except Exception as e:
        db.rollback()
        logger.error(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_notified_at_column()
