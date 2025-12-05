# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .helpers import format_date_for_api
from .service import BouncieService

logger = logging.getLogger(__name__)

# ------------------------------ CONSTANTS ------------------------------

CHUNK_DELTA_DAYS = 7
# ------------------------------ DATA FETCHING ------------------------------

async def fetch_trips_in_date_range(
    service: BouncieService,
    start_date: datetime,
    end_date: datetime,
    imei: Optional[str] = None,
    vehicles: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all Bouncie trips within a date range, handling API chunking automatically.
    
    Args:
        service: BouncieService instance
        start_date: Start date for fetching trips
        end_date: End date for fetching trips
        imei: IMEI to filter by specific vehicle
        vehicles: List of vehicles
    
    Returns:
        List of trip dictionaries
    """
    if vehicles is None:
        vehicles_result = await service.get_vehicles()
        if not vehicles_result.get("success"):
            logger.warning("Failed to fetch vehicles")
            return []
        vehicles = vehicles_result.get("data", []) or []
    
    if not vehicles:
        return []
    
    all_trips = []
    chunk_delta = timedelta(days=CHUNK_DELTA_DAYS)
    
    for vehicle in vehicles:
        vehicle_imei = vehicle.get("imei")
        if not vehicle_imei or (imei and vehicle_imei != imei):
            continue
        
        chunk_end = end_date
        while chunk_end > start_date:
            chunk_start = max(chunk_end - chunk_delta, start_date)
            
            trips_result = await service.get_trips(
                start_date=format_date_for_api(chunk_start),
                end_date=format_date_for_api(chunk_end),
                imei=vehicle_imei
            )
            
            if trips_result.get("success"):
                trips_data = trips_result.get("data", []) or []
                all_trips.extend(trips_data)
            
            chunk_end = chunk_start - timedelta(days=1)
    
    return all_trips

# ------------------------------ END OF FILE ------------------------------

