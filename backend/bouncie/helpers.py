# ------------------------------ IMPORTS ------------------------------
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import logging
import polyline
from core.database.models import Trip
from .constants import DEFAULT_TIME_BUFFER_HOURS

logger = logging.getLogger(__name__)

# ------------------------------ DATE/TIME PARSING ------------------------------

def parse_bouncie_datetime(iso_string: str) -> Optional[datetime]:
    if not iso_string:
        return None
    
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=None)
    
    except Exception:
        return None

def format_date_for_api(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")

# ------------------------------ GPS/POLYLINE CONVERSION ------------------------------

def get_trip_coordinates(trip: Dict[str, Any]) -> List[Tuple[float, float]]:
    gps = trip.get('gps')
    if not gps or not isinstance(gps, dict) or gps.get('type') != 'LineString':
        return []
    
    coords = gps.get('coordinates', [])
    if not isinstance(coords, list):
        return []
    
    result = []
    for c in coords:
        if not isinstance(c, (list, tuple)) or len(c) < 2:
            continue
        try:
            lon, lat = float(c[0]), float(c[1])
            result.append((lat, lon))
        except (ValueError, TypeError):
            continue
    
    return result

def get_trip_polyline(trip: Dict[str, Any]) -> Optional[str]:
    coords = get_trip_coordinates(trip)
    if not coords:
        return None
    return polyline.encode(coords, precision=5)

# ------------------------------ TRIP AGGREGATION ------------------------------

def aggregate_bouncie_trips(trips: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        distance = trip.get('distance')
        if distance is None:
            distance = 0
        else:
            try:
                distance = float(distance)
            except (ValueError, TypeError):
                distance = 0
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
    buffer_hours: int = None,
    imei: Optional[str] = None
) -> List[Dict[str, Any]]:
    if not trips:
        return []
    
    if buffer_hours is None:
        buffer_hours = DEFAULT_TIME_BUFFER_HOURS
    
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
    if not trips:
        return None
    
    if imei:
        trips = [t for t in trips if t.get('imei') == imei]
    
    valid_trips = []
    for trip in trips:
        trip_start = parse_bouncie_datetime(trip.get("startTime"))
        trip_end = parse_bouncie_datetime(trip.get("endTime"))
        if trip_start and trip_end:
            valid_trips.append((trip, trip_start, trip_end))
    
    if not valid_trips:
        return None
    
    for trip, trip_start, trip_end in valid_trips:
        if trip_start <= target_time <= trip_end:
            start_odometer = trip.get("startOdometer")
            end_odometer = trip.get("endOdometer")
            
            if start_odometer is None and end_odometer is None:
                continue
            
            if target_time == trip_start and start_odometer is not None:
                return {
                    "odometer": float(start_odometer),
                    "timestamp": target_time,
                    "source": "trip_start",
                    "trip_id": trip.get("transactionId")
                }
            
            if target_time == trip_end and end_odometer is not None:
                return {
                    "odometer": float(end_odometer),
                    "timestamp": target_time,
                    "source": "trip_end",
                    "trip_id": trip.get("transactionId")
                }
            
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
    
    trips_before = [(t, s, e) for t, s, e in valid_trips if e <= target_time]
    if trips_before:
        trips_before.sort(key=lambda x: x[2], reverse=True)
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
    
    trips_after = [(t, s, e) for t, s, e in valid_trips if s >= target_time]
    if trips_after:
        trips_after.sort(key=lambda x: x[1])
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

# ------------------------------ DATETIME UTILITIES ------------------------------

def ensure_utc_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def normalize_to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    return to_naive_utc(ensure_utc_datetime(dt))

def serialize_datetime(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj

# ------------------------------ MODEL SERIALIZATION ------------------------------

def trip_to_dict(trip: Trip) -> Dict[str, Any]:
    return {
        "trip_id": trip.trip_id,
        "vehicle_id": trip.vehicle_id,
        "start_date": trip.start_date,
        "start_time": trip.start_time,
        "end_date": trip.end_date,
        "end_time": trip.end_time,
        "kilometers_driven": trip.kilometers_driven,
        "status": trip.status,
        "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
    }


# ------------------------------ END OF FILE ------------------------------

