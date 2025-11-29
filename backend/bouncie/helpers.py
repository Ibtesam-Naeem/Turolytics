# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import polyline

logger = logging.getLogger(__name__)

# ------------------------------ DATE/TIME PARSING ------------------------------

def parse_bouncie_datetime(iso_string: str) -> Optional[datetime]:
    """Parse Bouncie ISO datetime string into datetime object."""
    if not iso_string:
        return None
    
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None)
   
    except Exception as e:
        logger.debug(f"Error parsing Bouncie datetime '{iso_string}': {e}")
        return None

def format_date_for_api(date: datetime) -> str:
    """Format datetime for Bouncie API (YYYY-MM-DD)."""
    return date.strftime("%Y-%m-%d")

# ------------------------------ GPS/POLYLINE CONVERSION ------------------------------

def get_trip_coordinates(trip: Dict[str, Any]) -> List[Tuple[float, float]]:
    """Extract coordinates from a Bouncie trip as (lat, lon) tuples."""
    gps = trip.get('gps')
    if not gps or not isinstance(gps, dict) or gps.get('type') != 'LineString':
        return []
    
    coords = gps.get('coordinates', [])
    return [(c[1], c[0]) for c in coords]

def get_trip_polyline(trip: Dict[str, Any]) -> Optional[str]:
    """Get encoded polyline string from a Bouncie trip."""
    coords = get_trip_coordinates(trip)
    if not coords:
        return None
    return polyline.encode(coords, precision=5)

# ------------------------------ TRIP AGGREGATION ------------------------------

def aggregate_bouncie_trips(trips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple Bouncie trips into summary statistics."""
    if not trips:
        return {
            "total_distance_miles": 0.0,
            "total_distance_km": 0.0,
            "earliest_start": None,
            "latest_end": None,
            "total_duration_hours": 0.0
        }
    
    total_distance_miles = 0.0
    starts = []
    ends = []
    
    for trip in trips:
        distance = trip.get('distance', 0) or 0
        total_distance_miles += distance
        
        start_dt = parse_bouncie_datetime(trip.get("startTime"))
        end_dt = parse_bouncie_datetime(trip.get("endTime"))
        if start_dt:
            starts.append(start_dt)
        if end_dt:
            ends.append(end_dt)
    
    earliest_start = min(starts) if starts else None
    latest_end = max(ends) if ends else None
    
    total_duration_hours = 0.0
    if earliest_start and latest_end:
        total_duration_hours = round((latest_end - earliest_start).total_seconds() / 3600, 2)
    
    return {
        "total_distance_miles": total_distance_miles,
        "total_distance_km": total_distance_miles * 1.60934,
        "earliest_start": earliest_start,
        "latest_end": latest_end,
        "total_duration_hours": total_duration_hours
    }

def filter_trips_by_date_range(
    trips: List[Dict[str, Any]], 
    start: datetime, 
    end: datetime,
    buffer_hours: int = 2,
    imei: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filter Bouncie trips that fall within a date range (with buffer)."""
    if not trips:
        return []
    
    buffer = timedelta(hours=buffer_hours)
    matching_trips = []
    
    for trip in trips:
        if imei and trip.get('imei') != imei:
            continue
        
        trip_start = parse_bouncie_datetime(trip.get("startTime"))
        trip_end = parse_bouncie_datetime(trip.get("endTime"))
        
        if not trip_start or not trip_end:
            continue
        
        if trip_start <= end + buffer and trip_end >= start - buffer:
            matching_trips.append(trip)
    
    return matching_trips


# ------------------------------ END OF FILE ------------------------------

