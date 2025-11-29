# ------------------------------ IMPORTS ------------------------------
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import polyline

from .helpers import (
    filter_trips_by_date_range,
    aggregate_bouncie_trips,
    get_trip_polyline,
    get_trip_coordinates
)
from turo.parsing import parse_turo_trip_datetime_from_dict

logger = logging.getLogger(__name__)

# ------------------------------ MATCHING FUNCTIONS ------------------------------

def _find_matching_trips(
    turo_trip: Dict[str, Any],
    bouncie_trips: List[Dict[str, Any]],
    vehicle_imei: Optional[str] = None,
    time_buffer_hours: int = 2
) -> Optional[Tuple[List[Dict[str, Any]], datetime, datetime]]:
    """Find Bouncie trips that match a Turo trip's time window."""
    if not bouncie_trips:
        return None
    
    if vehicle_imei:
        bouncie_trips = [t for t in bouncie_trips if t.get('imei') == vehicle_imei]
        if not bouncie_trips:
            return None
    
    turo_start = parse_turo_trip_datetime_from_dict(turo_trip, is_start=True)
    turo_end = parse_turo_trip_datetime_from_dict(turo_trip, is_start=False)
    
    if not turo_start or not turo_end:
        logger.warning(f"Could not parse Turo trip times for trip {turo_trip.get('trip_id')}")
        return None
    
    matching_trips = filter_trips_by_date_range(
        bouncie_trips,
        turo_start,
        turo_end,
        buffer_hours=time_buffer_hours,
        imei=vehicle_imei
    )
    
    if not matching_trips:
        return None
    
    return (matching_trips, turo_start, turo_end)

def _build_match_result(
    matching_trips: List[Dict[str, Any]],
    aggregated: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the match result structure with coordinates and polylines."""
    aggregated_trip = matching_trips[0].copy()
    aggregated_trip['aggregated_distance_miles'] = aggregated['total_distance_miles']
    aggregated_trip['aggregated_distance_km'] = aggregated['total_distance_km']
    aggregated_trip['trip_count'] = len(matching_trips)
    aggregated_trip['earliest_start'] = aggregated.get('earliest_start')
    aggregated_trip['latest_end'] = aggregated.get('latest_end')
    aggregated_trip['total_duration_hours'] = aggregated.get('total_duration_hours', 0.0)
    
    trips_with_polylines = []
    all_coordinates = []
    
    try:
        for trip in matching_trips:
            trip_copy = trip.copy()
            trip_coords = get_trip_coordinates(trip)
            trip_copy['polyline'] = get_trip_polyline(trip)
            trip_copy['coordinates'] = trip_coords if trip_coords else None
            trip_copy['coordinate_count'] = len(trip_coords)
            all_coordinates.extend(trip_coords)
            trips_with_polylines.append(trip_copy)
        
        aggregated_trip['all_trips'] = trips_with_polylines
        
        if all_coordinates:
            aggregated_trip['coordinates'] = all_coordinates
            aggregated_trip['coordinate_count'] = len(all_coordinates)
            aggregated_trip['polyline'] = polyline.encode(all_coordinates, precision=5)
        else:
            aggregated_trip['coordinates'] = None
            aggregated_trip['coordinate_count'] = 0
            aggregated_trip['polyline'] = None
            
    except Exception as e:
        logger.debug(f"Could not extract coordinates: {e}")
        aggregated_trip['all_trips'] = matching_trips
        aggregated_trip['coordinates'] = None
        aggregated_trip['coordinate_count'] = 0
    
    return aggregated_trip

def match_trip(
    turo_trip: Dict[str, Any],
    bouncie_trips: List[Dict[str, Any]],
    vehicle_imei: Optional[str] = None,
    time_buffer_hours: int = 2
) -> Optional[Dict[str, Any]]:
    """Match a Turo trip to the best matching Bouncie trip(s)."""
    match_data = _find_matching_trips(turo_trip, bouncie_trips, vehicle_imei, time_buffer_hours)
    if not match_data:
        return None
    
    matching_trips, turo_start, turo_end = match_data
    
    aggregated = aggregate_bouncie_trips(matching_trips)
    result = _build_match_result(matching_trips, aggregated)
    
    logger.info(
        f"Matched Turo trip {turo_trip.get('trip_id')} to {len(matching_trips)} "
        f"Bouncie trip(s) with total distance {aggregated['total_distance_km']:.1f} km"
    )
    
    return result

def match_all_trips(
    turo_trips: List[Dict[str, Any]],
    bouncie_trips: List[Dict[str, Any]],
    vehicle_imei_map: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Match multiple Turo trips to Bouncie trips."""
    results = []
    
    for turo_trip in turo_trips:
        imei = None
        if vehicle_imei_map:
            trip_id = turo_trip.get('trip_id')
            vehicle_id = turo_trip.get('vehicle_id')
            imei = vehicle_imei_map.get(trip_id) or vehicle_imei_map.get(vehicle_id)
        
        match_result = match_trip(turo_trip, bouncie_trips, imei)
        
        if match_result:
            results.append({
                "turo_trip": turo_trip,
                "matched_bouncie_trip": match_result
            })
        else:
            results.append({
                "turo_trip": turo_trip,
                "matched_bouncie_trip": None
            })
    
    return results

# ------------------------------ END OF FILE ------------------------------

