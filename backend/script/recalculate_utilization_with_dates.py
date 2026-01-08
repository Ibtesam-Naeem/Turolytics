#!/usr/bin/env python3
"""
Recalculate utilization history records to account for listed_on_turo_date and removed_from_turo_date.
This script updates all existing VehicleUtilizationHistory records with the corrected calculations.
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


def recalculate_utilization_with_dates(year: int = None):
    """
    Recalculate utilization for all vehicles, accounting for listed_on_turo_date and removed_from_turo_date.
    
    Args:
        year: Year to recalculate (defaults to current year if None)
    """
    db = SessionLocal()
    try:
        if year is None:
            year = datetime.now(timezone.utc).year
        
        logger.info(f"Recalculating utilization for year {year} with date filtering...")
        
        # Get all vehicles
        vehicles = db.query(Vehicle).all()
        logger.info(f"Found {len(vehicles)} vehicles to process")
        
        # Get all accounts
        accounts = {acc.id: acc for acc in db.query(Account).all()}
        
        # Create TuroDataService instance
        service = TuroDataService(db)
        
        updated_count = 0
        created_count = 0
        
        for vehicle in vehicles:
            account = accounts.get(vehicle.account_id)
            if not account:
                logger.warning(f"  No account found for vehicle {vehicle.id}, skipping...")
                continue
            
            logger.info(f"Processing vehicle {vehicle.id} ({vehicle.name})...")
            if vehicle.listed_on_turo_date:
                logger.info(f"  Listed on: {vehicle.listed_on_turo_date.date()}")
            if vehicle.removed_from_turo_date:
                logger.info(f"  Removed on: {vehicle.removed_from_turo_date.date()}")
            
            for month in range(1, 13):
                try:
                    # Calculate utilization for this month using updated logic
                    utilization_value, booked_days, total_days = service._calculate_monthly_utilization(
                        vehicle_id=vehicle.id,
                        account=account,
                        year=year,
                        month=month
                    )
                    
                    # Check if record already exists
                    existing = db.query(VehicleUtilizationHistory).filter(
                        VehicleUtilizationHistory.vehicle_id == vehicle.id,
                        VehicleUtilizationHistory.account_id == account.id,
                        VehicleUtilizationHistory.year == year,
                        VehicleUtilizationHistory.month == month
                    ).first()
                    
                    if existing:
                        # Update existing record
                        old_utilization = existing.utilization
                        existing.booked_days = booked_days
                        existing.total_days = total_days
                        existing.calculated_at = datetime.now(timezone.utc)
                        new_utilization = existing.utilization
                        
                        if abs(old_utilization - new_utilization) > 0.1:  # Only log if significant change
                            logger.info(f"  Updated {month}/{year}: {old_utilization:.1f}% → {new_utilization:.1f}% ({booked_days}/{total_days} days)")
                        updated_count += 1
                    else:
                        # Create new record
                        history_record = VehicleUtilizationHistory(
                            vehicle_id=vehicle.id,
                            account_id=account.id,
                            year=year,
                            month=month,
                            booked_days=booked_days,
                            total_days=total_days,
                            calculated_at=datetime.now(timezone.utc)
                        )
                        db.add(history_record)
                        logger.info(f"  Created {month}/{year}: {history_record.utilization:.1f}% ({booked_days}/{total_days} days)")
                        created_count += 1
                    
                except Exception as e:
                    logger.warning(f"  Failed to calculate utilization for {month}/{year}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
            
            # Commit after each vehicle
            db.commit()
            logger.info(f"✓ Completed vehicle {vehicle.id}")
        
        logger.info(f"✓ Recalculation complete!")
        logger.info(f"  Updated: {updated_count} records")
        logger.info(f"  Created: {created_count} records")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error recalculating utilization: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recalculate utilization history with date filtering")
    parser.add_argument("--year", type=int, default=None, help="Year to recalculate (defaults to current year)")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Recalculating Utilization History with Date Filtering")
    logger.info("=" * 60)
    
    recalculate_utilization_with_dates(year=args.year)
    
    logger.info("=" * 60)
    logger.info("✓ Recalculation completed successfully!")
