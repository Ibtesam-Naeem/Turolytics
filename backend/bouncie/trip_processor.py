# ------------------------------ IMPORTS ------------------------------
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .service import BouncieService
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_all_trips
from .helpers import trip_to_dict, ensure_utc_datetime, serialize_datetime, to_naive_utc
from .constants import DEFAULT_SYNC_DAYS_BACK
from turo.parsing import parse_turo_trip_datetime_from_dict
from core.database.models import (
    Account, Vehicle, Trip, BouncieIntegration,
    BouncieVehicleMapping, BouncieTripMatch
)
from core.database.db_service import DatabaseService

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def _find_matching_turo_vehicle(
    bouncie_vehicle: Dict[str, Any],
    turo_vehicles: List[Vehicle],
    mapped_vehicle_ids: Set[int]
) -> Optional[Vehicle]:
    bouncie_nickname = (bouncie_vehicle.get("nickName") or "").lower().strip()
    
    if bouncie_nickname:
        for tv in turo_vehicles:
            if tv.id in mapped_vehicle_ids or not tv.name:
                continue
            
            turo_name_lower = tv.name.lower()
            if bouncie_nickname in turo_name_lower:
                logger.info(f"Matched '{bouncie_vehicle.get('nickName')}' to '{tv.name}'")
                return tv
            
            words = [w for w in bouncie_nickname.split() if len(w) > 2]
            if words and all(word in turo_name_lower for word in words):
                logger.info(f"Matched '{bouncie_vehicle.get('nickName')}' to '{tv.name}' by words")
                return tv
    
    unmapped = [tv for tv in turo_vehicles if tv.id not in mapped_vehicle_ids]
    if len(unmapped) == 1:
        logger.warning(f"No name match for '{bouncie_vehicle.get('nickName')}', using only unmapped vehicle '{unmapped[0].name}'")
        return unmapped[0]
    elif len(unmapped) > 1:
        logger.warning(f"No name match for '{bouncie_vehicle.get('nickName')}' and {len(unmapped)} unmapped vehicles - requires manual mapping")
    
    return None

def _get_trip_dedup_key(trip: Dict[str, Any]) -> Optional[tuple]:
    start_time = trip.get("startTime")
    end_time = trip.get("endTime")
    imei = trip.get("imei")
    transaction_id = trip.get("transactionId")
    
    if transaction_id:
        return ("id", transaction_id)
    if start_time and end_time and imei:
        return ("time", start_time, end_time, imei)
    return None

async def _fill_gap_trips(
    service: BouncieService,
    unmatched: List[Dict[str, Any]],
    all_bouncie_trips: List[Dict[str, Any]],
    bouncie_vehicles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    gap_trips = []
    for match in unmatched:
        turo_trip = match.get("turo_trip")
        if not turo_trip:
            continue
        
        turo_start_raw = parse_turo_trip_datetime_from_dict(turo_trip, is_start=True)
        turo_end_raw = parse_turo_trip_datetime_from_dict(turo_trip, is_start=False)
        
        if turo_start_raw and turo_end_raw:
            turo_start_utc = ensure_utc_datetime(turo_start_raw)
            turo_end_utc = ensure_utc_datetime(turo_end_raw)
            gap_trips.extend(await fetch_trips_in_date_range(
                service=service,
                start_date=turo_start_utc - timedelta(days=1),
                end_date=turo_end_utc + timedelta(days=1),
                vehicles=bouncie_vehicles
            ))
    
    if not gap_trips:
        return all_bouncie_trips
    
    existing_keys = {
        _get_trip_dedup_key(t) for t in all_bouncie_trips
        if _get_trip_dedup_key(t) is not None
    }
    new_trips = [
        t for t in gap_trips
        if _get_trip_dedup_key(t) not in existing_keys
    ]
    
    if new_trips:
        all_bouncie_trips.extend(new_trips)
        logger.info(f"Added {len(new_trips)} new trips from gap fill")
    
    return all_bouncie_trips

def _save_match_results(
    db: Session,
    account: Account,
    matches: List[Dict[str, Any]],
    results: Dict[str, Any]
) -> None:
    for match in matches:
        turo_trip_dict = match.get("turo_trip")
        matched_bouncie = match.get("matched_bouncie_trip")
        
        if not matched_bouncie:
            continue
        
        trip = db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.trip_id == turo_trip_dict.get("trip_id")
        ).first()
        
        if not trip:
            continue
        
        existing_match = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.trip_id == trip.id
        ).first()
        
        serialized_data = serialize_datetime(matched_bouncie)
        
        if existing_match:
            match_obj = existing_match
            results["matches_updated"] += 1
        else:
            match_obj = BouncieTripMatch(account_id=account.id, trip_id=trip.id)
            db.add(match_obj)
            results["matches_created"] += 1
        
        match_obj.bouncie_trip_count = matched_bouncie.get("trip_count", 0)
        match_obj.aggregated_distance_km = matched_bouncie.get("aggregated_distance_km")
        match_obj.aggregated_distance_miles = matched_bouncie.get("aggregated_distance_miles")
        match_obj.total_duration_hours = matched_bouncie.get("total_duration_hours")
        match_obj.coordinates = matched_bouncie.get("coordinates")
        match_obj.polyline = matched_bouncie.get("polyline")
        match_obj.coordinate_count = matched_bouncie.get("coordinate_count", 0)
        
        earliest_start = matched_bouncie.get("earliest_start")
        latest_end = matched_bouncie.get("latest_end")
        match_obj.bouncie_earliest_start = ensure_utc_datetime(earliest_start) if earliest_start else None
        match_obj.bouncie_latest_end = ensure_utc_datetime(latest_end) if latest_end else None
        
        match_obj.match_data = serialized_data

# ------------------------------ AUTOMATIC PROCESSING ------------------------------

async def process_bouncie_link(
    db: Session,
    account_id: int,
    days_back: int = DEFAULT_SYNC_DAYS_BACK,
    skip_existing_matches: bool = True,
    force_rematch: bool = False
) -> Dict[str, Any]:
    try:
        account = DatabaseService.get_account_or_raise(db, account_id=account_id)
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
        if not integration:
            return {"success": False, "error": "Bouncie not linked for this account"}
        
        service = BouncieService(db=db, account_id=account_id)
        service._load_tokens()
        
        if not service.access_token:
            return {"success": False, "error": "No access token. Please reconnect Bouncie."}
        
        if service.token_expires_at and service.token_expires_at < datetime.now(timezone.utc):
            if not service.refresh_token:
                return {"success": False, "error": "Token expired. Please reconnect Bouncie."}
            logger.info(f"Refreshing expired token for account {account_id}")
            if not service._refresh_access_token():
                return {"success": False, "error": "Token refresh failed. Please reconnect Bouncie."}
        
        results = {
            "vehicles_mapped": 0,
            "trips_fetched": 0,
            "trips_matched": 0,
            "trips_skipped": 0,
            "matches_created": 0,
            "matches_updated": 0,
            "errors": []
        }

        vehicles_result = await service.get_vehicles()
        if not vehicles_result.get("success"):
            error_msg = f"Failed to fetch vehicles: {vehicles_result.get('error')}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return {"success": False, "results": results}
        
        bouncie_vehicles = vehicles_result.get("data", [])
        logger.info(f"Found {len(bouncie_vehicles)} Bouncie vehicle(s)")
        
        turo_vehicles = db.query(Vehicle).filter(Vehicle.account_id == account.id).all()
        
        existing_mappings = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        ).all()
        mapped_vehicle_ids = {m.vehicle_id for m in existing_mappings}
        mapped_imeis = {m.imei for m in existing_mappings}
        vehicle_imei_map = {m.vehicle_id: m.imei for m in existing_mappings}
        
        for bv in bouncie_vehicles:
            imei = bv.get("imei")
            if not imei or imei in mapped_imeis:
                continue
            
            turo_vehicle = _find_matching_turo_vehicle(bv, turo_vehicles, mapped_vehicle_ids)
            if turo_vehicle:
                mapping = BouncieVehicleMapping(
                    account_id=account.id,
                    vehicle_id=turo_vehicle.id,
                    imei=imei,
                    bouncie_nickname=bv.get("nickName"),
                    bouncie_vin=bv.get("vin")
                )
                db.add(mapping)
                mapped_vehicle_ids.add(turo_vehicle.id)
                mapped_imeis.add(imei)
                vehicle_imei_map[turo_vehicle.id] = imei
                results["vehicles_mapped"] += 1
                logger.info(f"Mapped IMEI {imei} to vehicle {turo_vehicle.id} ({turo_vehicle.name})")
        
        db.commit()
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        all_bouncie_trips = await fetch_trips_in_date_range(
            service=service,
            start_date=start_date,
            end_date=end_date,
            vehicles=bouncie_vehicles
        )
        
        results["trips_fetched"] = len(all_bouncie_trips)
        logger.info(f"Fetched {len(all_bouncie_trips)} Bouncie trip(s)")
        
        if not all_bouncie_trips:
            return {"success": True, "results": results, "message": "No Bouncie trips found"}
        
        turo_trips = db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.status == "COMPLETED"
        ).all()
        
        trips_in_range = []
        for trip in turo_trips:
            trip_dict = trip_to_dict(trip)
            trip_start = parse_turo_trip_datetime_from_dict(trip_dict, is_start=True)
            trip_end = parse_turo_trip_datetime_from_dict(trip_dict, is_start=False)
            
            if trip_start and trip_end:
                trip_start_utc = ensure_utc_datetime(trip_start)
                trip_end_utc = ensure_utc_datetime(trip_end)
                
                if trip_start_utc <= end_date and trip_end_utc >= start_date:
                    trips_in_range.append(trip)
        
        if not trips_in_range:
            return {"success": True, "results": results, "message": "No Turo trips found in date range to match"}
        
        if skip_existing_matches and not force_rematch:
            existing_match_trip_ids = {
                match.trip_id for match in db.query(BouncieTripMatch)
                .join(Trip, BouncieTripMatch.trip_id == Trip.id)
                .filter(Trip.account_id == account.id)
                .all()
            }
            trips_to_match = [t for t in trips_in_range if t.id not in existing_match_trip_ids]
            results["trips_skipped"] = len(trips_in_range) - len(trips_to_match)
            logger.info(f"Found {len(trips_to_match)} unmatched trips, skipping {results['trips_skipped']}")
        else:
            trips_to_match = trips_in_range
            if force_rematch:
                logger.info(f"Force re-matching {len(trips_to_match)} trips")
        
        if not trips_to_match:
            return {
                "success": True,
                "results": results,
                "message": "All trips already have matches. Use force_rematch=True to re-match."
            }
        
        turo_trips_dict = [trip_to_dict(t) for t in trips_to_match]
        
        logger.info(f"Matching {len(turo_trips_dict)} Turo trips with {len(all_bouncie_trips)} Bouncie trips")
        matches = match_all_trips(turo_trips_dict, all_bouncie_trips, vehicle_imei_map)
        
        unmatched = [m for m in matches if not m.get("matched_bouncie_trip")]
        if unmatched and len(unmatched) <= 5:
            logger.info(f"Found {len(unmatched)} unmatched trips, attempting gap fill...")
            all_bouncie_trips = await _fill_gap_trips(service, unmatched, all_bouncie_trips, bouncie_vehicles)
            matches = match_all_trips(turo_trips_dict, all_bouncie_trips, vehicle_imei_map)
        
        results["trips_matched"] = len([m for m in matches if m.get("matched_bouncie_trip")])
        _save_match_results(db, account, matches, results)
        
        db.commit()
        
        logger.info(f"Processing complete: {results}")
        return {"success": True, "results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing Bouncie link: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}


async def handle_bouncie_auto_processing(db: Session, account_id: int) -> None:
    try:
        result = await process_bouncie_link(db, account_id, days_back=DEFAULT_SYNC_DAYS_BACK)
        if result.get("success"):
            r = result.get("results", {})
            logger.info(
                f"Auto-processing: {r.get('vehicles_mapped')} vehicles, "
                f"{r.get('trips_fetched')} trips, {r.get('matches_created')} matches"
            )
        else:
            logger.warning(f"Auto-processing failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error during auto-processing: {e}")

# ------------------------------ END OF FILE ------------------------------
