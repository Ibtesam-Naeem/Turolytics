# ------------------------------ IMPORTS ------------------------------
from typing import Dict, Any
from core.database.models import Trip


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


# ------------------------------ END OF FILE ------------------------------

