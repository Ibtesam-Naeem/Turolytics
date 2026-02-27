# ------------------------------ IMPORTS ------------------------------
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# ------------------------------ TURO DATE/TIME PARSING ------------------------------

def _parse_turo_time(time_str: str) -> Optional[Tuple[int, int]]:
    """Parse Turo time string (e.g., '4:30 p.m.') into (hour, minute) tuple."""
    if not time_str:
        return None
    
    try:
        normalized = time_str.strip().replace('.', '').upper()
        parsed = datetime.strptime(normalized, "%I:%M %p")
        return (parsed.hour, parsed.minute)
    except Exception as e:
        logger.debug(f"Error parsing time '{time_str}': {e}")
        return None

def _parse_turo_date(date_str: str, reference_year: Optional[int] = None) -> Optional[datetime]:
    """Parse Turo date string (e.g., 'Sat, Nov 1') into datetime object."""
    if not date_str:
        return None
    
    if reference_year is None:
        reference_year = datetime.now().year
    
    try:
        parsed = datetime.strptime(date_str.strip(), "%a, %b %d")
        return parsed.replace(year=reference_year)
    except Exception as e:
        logger.debug(f"Error parsing date '{date_str}': {e}")
        return None

def _parse_turo_trip_datetime(
    date_str: str,
    time_str: str,
    reference_year: Optional[int] = None
) -> Optional[datetime]:
    """Parse Turo trip date and time into a single datetime object."""
    date_obj = _parse_turo_date(date_str, reference_year)
    time_tuple = _parse_turo_time(time_str)
    
    if not date_obj or not time_tuple:
        return None
    
    hour, minute = time_tuple
    return date_obj.replace(hour=hour, minute=minute)

def parse_turo_trip_datetime_from_dict(
    turo_trip: Dict[str, Any],
    is_start: bool = True
) -> Optional[datetime]:
    """Parse Turo trip start or end datetime from trip dictionary."""
    date_key = 'start_date' if is_start else 'end_date'
    time_key = 'start_time' if is_start else 'end_time'
    
    date_str = turo_trip.get(date_key, '')
    time_str = turo_trip.get(time_key, '')
    
    if not date_str:
        return None

    updated_at = turo_trip.get('updated_at')
    if updated_at:
        try:
            updated_datetime = datetime.fromisoformat(str(updated_at).replace('Z', '+00:00'))
            reference_year = updated_datetime.year

            parsed_date = _parse_turo_date(date_str, reference_year)
            if parsed_date:
                updated_month = updated_datetime.month
                parsed_month = parsed_date.month

                if updated_month <= 3:
                    if parsed_month >= 4:
                        reference_year = reference_year - 1
                elif updated_month >= 10:
                    pass
        except Exception:
            reference_year = datetime.now().year
    else:
        reference_year = datetime.now().year
    
    return _parse_turo_trip_datetime(date_str, time_str, reference_year)

# ------------------------------ END OF FILE ------------------------------

