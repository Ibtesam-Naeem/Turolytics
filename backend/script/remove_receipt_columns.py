#!/usr/bin/env python3
"""
Migration script to remove columns from turo_receipts table:
- trip_id (foreign key)
- host_name
- guest_id
- cost_details
- scraped_at
- earnings_breakdown

Also cleans vehicle_name to remove year (e.g., "Hyundai Elantra2017" -> "Hyundai Elantra")
"""

import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from core.database.connection import engine, SessionLocal
from core.database.models import Receipt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_vehicle_name(vehicle_name: str):
    """Extract year from vehicle name and return cleaned name and year separately."""
    if not vehicle_name:
        return vehicle_name, None
    
    # Look for 4-digit year at the end (1900-2099)
    year_match = re.search(r'(\d{4})$', vehicle_name.strip())
    if year_match:
        year = year_match.group(1)
        cleaned_name = vehicle_name[:year_match.start()].strip()
        return cleaned_name, year
    
    return vehicle_name, None


def remove_receipt_columns():
    """Remove specified columns from turo_receipts table."""
    db = SessionLocal()
    try:
        # Check if table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'turo_receipts' not in tables:
            logger.info("✓ Table 'turo_receipts' does not exist, nothing to migrate")
            return
        
        # Get current columns
        columns = inspector.get_columns('turo_receipts')
        column_names = [col['name'] for col in columns]
        
        logger.info(f"Current columns in turo_receipts: {column_names}")
        
        # Clean vehicle_name data first (remove year from vehicle_name)
        logger.info("Cleaning vehicle_name data (removing year)...")
        receipts = db.query(Receipt).all()
        updated_count = 0
        for receipt in receipts:
            if receipt.vehicle_name:
                cleaned_name, extracted_year = clean_vehicle_name(receipt.vehicle_name)
                if cleaned_name != receipt.vehicle_name:
                    receipt.vehicle_name = cleaned_name
                    if extracted_year and not receipt.vehicle_year:
                        receipt.vehicle_year = extracted_year
                    updated_count += 1
        
        if updated_count > 0:
            db.commit()
            logger.info(f"✓ Cleaned {updated_count} vehicle_name entries")
        
        # Remove columns
        columns_to_remove = ['trip_id', 'host_name', 'guest_id', 'cost_details', 'scraped_at', 'earnings_breakdown', 'kilometers_driven']
        
        for column_name in columns_to_remove:
            if column_name in column_names:
                logger.info(f"Removing column '{column_name}'...")
                
                # Drop foreign key constraint if it's trip_id
                if column_name == 'trip_id':
                    try:
                        # Get foreign key constraints
                        fk_constraints = inspector.get_foreign_keys('turo_receipts')
                        for fk in fk_constraints:
                            if 'trip_id' in fk.get('constrained_columns', []):
                                fk_name = fk.get('name')
                                if fk_name:
                                    db.execute(text(f"ALTER TABLE turo_receipts DROP CONSTRAINT IF EXISTS {fk_name}"))
                                    logger.info(f"  Dropped foreign key constraint: {fk_name}")
                    except Exception as e:
                        logger.warning(f"  Could not drop foreign key constraint: {e}")
                    
                    # Drop index if it exists
                    try:
                        db.execute(text("DROP INDEX IF EXISTS idx_receipt_trip"))
                        logger.info("  Dropped index: idx_receipt_trip")
                    except Exception as e:
                        logger.debug(f"  Index idx_receipt_trip may not exist: {e}")
                
                # Drop the column
                db.execute(text(f"ALTER TABLE turo_receipts DROP COLUMN IF EXISTS {column_name}"))
                db.commit()
                logger.info(f"✓ Removed column '{column_name}'")
            else:
                logger.info(f"✓ Column '{column_name}' does not exist, skipping")
        
        logger.info("✓ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during migration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        remove_receipt_columns()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
