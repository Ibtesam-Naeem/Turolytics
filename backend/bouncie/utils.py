# ------------------------------ IMPORTS ------------------------------
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from core.database.models import Trip, Account
from core.database.db_service import DatabaseService


# ------------------------------ HELPERS ------------------------------

def trip_to_dict(trip: Trip) -> Dict[str, Any]:
    """Convert Trip SQL model into serialisable dict for matching."""
    return {
        "trip_id": trip.trip_id,
        "vehicle_id": trip.vehicle_id,
        "start_date": trip.start_date,
        "start_time": trip.start_time,
        "end_date": trip.end_date,
        "end_time": trip.end_time,
        "kilometers_driven": trip.kilometers_driven,
        "status": trip.status,
        "scraped_at": trip.scraped_at.isoformat() if trip.scraped_at else None,
    }

def get_account_or_raise(db: Session, account_id: int = None, user_id: int = None) -> Account:
    """Get account by ID or user_id, raise HTTPException if not found."""
    from core.database.db_service import DatabaseService
    return DatabaseService.get_account_or_raise(db, account_id=account_id, user_id=user_id)


# ------------------------------ END OF FILE ------------------------------

