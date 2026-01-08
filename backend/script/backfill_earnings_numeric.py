#!/usr/bin/env python3
"""
Backfill earnings_amount_numeric for existing VehicleEarnings records.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import SessionLocal
from core.database.models import VehicleEarnings
from core.utils.route_helpers import parse_amount
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_earnings_numeric():
    """Backfill earnings_amount_numeric for records where it's None."""
    db = SessionLocal()
    try:
        # Update VehicleEarnings
        vehicle_earnings = db.query(VehicleEarnings).filter(
            VehicleEarnings.earnings_amount_numeric.is_(None)
        ).all()
        
        logger.info(f"Found {len(vehicle_earnings)} VehicleEarnings records with NULL earnings_amount_numeric")
        
        updated_count = 0
        for ve in vehicle_earnings:
            if ve.earnings_amount:
                numeric_value = parse_amount(ve.earnings_amount)
                if numeric_value is not None:
                    ve.earnings_amount_numeric = numeric_value
                    updated_count += 1
        
        db.commit()
        logger.info(f"✓ Updated {updated_count} VehicleEarnings records")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error backfilling earnings_amount_numeric: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_earnings_numeric()



