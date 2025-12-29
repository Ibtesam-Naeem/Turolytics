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

# ------------------------------ ODOMETER UTILITIES ------------------------------

def get_odometer_at_time_from_trips(
    trips: List[Dict[str, Any]],
    target_time: datetime,
    imei: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get odometer reading at a specific timestamp from Bouncie trips.
    
    Args:
        trips: List of Bouncie trip dictionaries
        target_time: Target datetime to get odometer reading
        imei: Optional IMEI to filter trips
    
    Returns:
        Dict with odometer reading and metadata, or None if not found
        {
            "odometer": float,
            "timestamp": datetime,
            "source": "trip_start" | "trip_end" | "interpolated" | "last_trip_before" | "first_trip_after",
            "trip_id": str (optional)
        }
    """
    if not trips:
        return None
    
    # Filter by IMEI if provided
    if imei:
        trips = [t for t in trips if t.get('imei') == imei]
    
    # Find trip that contains target_time
    for trip in trips:
        trip_start = parse_bouncie_datetime(trip.get("startTime"))
        trip_end = parse_bouncie_datetime(trip.get("endTime"))
        
        if not trip_start or not trip_end:
            continue
        
        # If target_time is within this trip
        if trip_start <= target_time <= trip_end:
            start_odometer = trip.get("startOdometer")
            end_odometer = trip.get("endOdometer")
            
            if start_odometer is None and end_odometer is None:
                continue
            
            # If exactly at start
            if target_time == trip_start and start_odometer is not None:
                return {
                    "odometer": float(start_odometer),
                    "timestamp": target_time,
                    "source": "trip_start",
                    "trip_id": trip.get("transactionId")
                }
            
            # If exactly at end
            if target_time == trip_end and end_odometer is not None:
                return {
                    "odometer": float(end_odometer),
                    "timestamp": target_time,
                    "source": "trip_end",
                    "trip_id": trip.get("transactionId")
                }
            
            # Interpolate between start and end
            if start_odometer is not None and end_odometer is not None:
                trip_duration = (trip_end - trip_start).total_seconds()
                time_elapsed = (target_time - trip_start).total_seconds()
                
                if trip_duration > 0:
                    ratio = time_elapsed / trip_duration
                    odometer = start_odometer + (end_odometer - start_odometer) * ratio
                    return {
                        "odometer": float(odometer),
                        "timestamp": target_time,
                        "source": "interpolated",
                        "trip_id": trip.get("transactionId")
                    }
    
    # No trip contains target_time - find nearest trip
    # Build list of valid trips with parsed timestamps
    valid_trips = []
    for trip in trips:
        trip_start = parse_bouncie_datetime(trip.get("startTime"))
        trip_end = parse_bouncie_datetime(trip.get("endTime"))
        if trip_start and trip_end:
            valid_trips.append((trip, trip_start, trip_end))
    
    if not valid_trips:
        return None
    
    # Find last trip before target_time
    trips_before = [(t, s, e) for t, s, e in valid_trips if e <= target_time]
    if trips_before:
        trips_before.sort(key=lambda x: x[2], reverse=True)  # Sort by endTime desc
        trip, _, trip_end = trips_before[0]
        end_odometer = trip.get("endOdometer")
        if end_odometer is not None:
            return {
                "odometer": float(end_odometer),
                "timestamp": trip_end,
                "source": "last_trip_before",
                "trip_id": trip.get("transactionId"),
                "note": f"Odometer from last trip before target time ({target_time})"
            }
    
    # Find first trip after target_time
    trips_after = [(t, s, e) for t, s, e in valid_trips if s >= target_time]
    if trips_after:
        trips_after.sort(key=lambda x: x[1])  # Sort by startTime asc
        trip, trip_start, _ = trips_after[0]
        start_odometer = trip.get("startOdometer")
        if start_odometer is not None:
            return {
                "odometer": float(start_odometer),
                "timestamp": trip_start,
                "source": "first_trip_after",
                "trip_id": trip.get("transactionId"),
                "note": f"Odometer from first trip after target time ({target_time})"
            }
    
    return None


# ------------------------------ END OF FILE ------------------------------

