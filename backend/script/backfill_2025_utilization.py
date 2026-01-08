#!/usr/bin/env python3
"""
Backfill utilization for all months in 2025.
Calculates and stores monthly utilization for each vehicle in 2025.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import SessionLocal
from core.database.models import Vehicle, VehicleUtilizationHistory, Account
from turo.service import TuroDataService
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_2025_utilization():
    """Calculate and store utilization for all months in 2025."""
    db = SessionLocal()
    try:
        vehicles = db.query(Vehicle).all()
        logger.info(f"Found {len(vehicles)} vehicles to process")
        
        total_records = 0
        for vehicle in vehicles:
            logger.info(f"Processing vehicle {vehicle.id} ({vehicle.name})...")
            
            # Get account for this vehicle
            account = db.query(Account).filter(Account.id == vehicle.account_id).first()
            if not account:
                logger.warning(f"  No account found for vehicle {vehicle.id}, skipping...")
                continue
            
            # Create TuroDataService instance
            service = TuroDataService(db)
            
            for month in range(1, 13):
                try:
                    # Calculate utilization for this month using TuroDataService
                    utilization_value, booked_days, total_days = service._calculate_monthly_utilization(
                        vehicle_id=vehicle.id,
                        account=account,
                        year=2025,
                        month=month
                    )
                    
                    # Check if record already exists (UNIQUE constraint ensures one per vehicle/year/month)
                    existing = db.query(VehicleUtilizationHistory).filter(
                        VehicleUtilizationHistory.vehicle_id == vehicle.id,
                        VehicleUtilizationHistory.account_id == account.id,
                        VehicleUtilizationHistory.year == 2025,
                        VehicleUtilizationHistory.month == month
                    ).first()
                    
                    if existing:
                        # Update existing record (utilization computed automatically)
                        existing.booked_days = booked_days
                        existing.total_days = total_days
                        existing.calculated_at = datetime.now(timezone.utc)
                        logger.info(f"  Updated {month}/2025: {existing.utilization:.1f}% ({booked_days}/{total_days} days)")
                    else:
                        # Create new record (utilization computed automatically)
                        history_record = VehicleUtilizationHistory(
                            vehicle_id=vehicle.id,
                            account_id=account.id,
                            year=2025,
                            month=month,
                            booked_days=booked_days,
                            total_days=total_days,
                            calculated_at=datetime.now(timezone.utc)
                        )
                        db.add(history_record)
                        logger.info(f"  Created {month}/2025: {history_record.utilization:.1f}% ({booked_days}/{total_days} days)")
                        total_records += 1
                    
                except Exception as e:
                    logger.warning(f"  Failed to calculate utilization for {month}/2025: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
            
            # Commit after each vehicle
            db.commit()
            logger.info(f"✓ Completed vehicle {vehicle.id}")
        
        logger.info(f"✓ Created/updated {total_records} utilization history records for 2025")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error backfilling 2025 utilization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting backfill: Utilization for 2025")
    logger.info("=" * 60)
    backfill_2025_utilization()
    logger.info("=" * 60)
    logger.info("✓ Backfill completed successfully!")

