#!/usr/bin/env python3
"""
Recalculate utilization for all vehicles using the fixed date parsing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import SessionLocal
from core.database.models import Vehicle
from core.database.db_service import DatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def recalculate_all_utilization():
    """Recalculate utilization for all vehicles."""
    db = SessionLocal()
    try:
        vehicles = db.query(Vehicle).all()
        logger.info(f"Found {len(vehicles)} vehicles to process")
        
        updated_count = 0
        for vehicle in vehicles:
            try:
                DatabaseService._calculate_and_update_utilization(db, vehicle, vehicle.account, period_days=30)
                updated_count += 1
                logger.info(f"✓ Updated utilization for vehicle {vehicle.id} ({vehicle.name}): {vehicle.utilization}%")
            except Exception as e:
                logger.warning(f"Failed to calculate utilization for vehicle {vehicle.id}: {e}")
        
        db.commit()
        logger.info(f"✓ Recalculated utilization for {updated_count} vehicles")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error recalculating utilization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    recalculate_all_utilization()



