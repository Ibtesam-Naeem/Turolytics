# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .helpers import format_date_for_api
from .service import BouncieService
from .constants import CHUNK_DELTA_DAYS

logger = logging.getLogger(__name__)

# ------------------------------ DATA FETCHING ------------------------------

async def fetch_trips_in_date_range(
    service: BouncieService,
    start_date: datetime,
    end_date: datetime,
    imei: Optional[str] = None,
    vehicles: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    if vehicles is None:
        vehicles_result = await service.get_vehicles()
        if not vehicles_result.get("success"):
            logger.warning("Failed to fetch vehicles")
            return []
        vehicles = vehicles_result.get("data", [])
    
    if not vehicles:
        return []
    
    all_trips = []
    chunk_delta = timedelta(days=CHUNK_DELTA_DAYS)
    failed_chunks = []
    
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
                trips_data = trips_result.get("data", [])
                all_trips.extend(trips_data)
            else:
                failed_chunks.append((chunk_start, chunk_end, vehicle_imei))
                logger.warning(
                    f"Failed to fetch Bouncie trips for chunk {format_date_for_api(chunk_start)} to "
                    f"{format_date_for_api(chunk_end)}: {trips_result.get('error')}"
                )
            
            chunk_end = chunk_start - timedelta(days=1)
    
    if failed_chunks:
        logger.info(f"Retrying {len(failed_chunks)} failed chunk(s)...")
        for chunk_start, chunk_end, vehicle_imei in failed_chunks:
            trips_result = await service.get_trips(
                start_date=format_date_for_api(chunk_start),
                end_date=format_date_for_api(chunk_end),
                imei=vehicle_imei
            )
            
            if trips_result.get("success"):
                trips_data = trips_result.get("data", [])
                all_trips.extend(trips_data)
                logger.info(
                    f"Successfully fetched {len(trips_data)} trips on retry for "
                    f"{format_date_for_api(chunk_start)} to {format_date_for_api(chunk_end)}"
                )
            else:
                logger.error(
                    f"Retry failed for chunk {format_date_for_api(chunk_start)} to "
                    f"{format_date_for_api(chunk_end)}: {trips_result.get('error')}"
                )
    
    return all_trips

# ------------------------------ END OF FILE ------------------------------

