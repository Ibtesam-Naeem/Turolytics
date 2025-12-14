# ------------------------------ IMPORTS ------------------------------
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from .service import BouncieService
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_all_trips
from .utils import trip_to_dict, get_account_or_raise
from core.database.models import (
    Account, Vehicle, Trip, BouncieIntegration,
    BouncieVehicleMapping, BouncieTripMatch
)
from core.database.db_service import DatabaseService

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def _serialize_datetime_for_json(obj: Any) -> Any:
    """Recursively serialize datetime objects to ISO format strings for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _serialize_datetime_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_datetime_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_serialize_datetime_for_json(item) for item in obj)
    else:
        return obj

def _set_match_fields(match: BouncieTripMatch, matched_bouncie: Dict[str, Any], serialized_match_data: Dict[str, Any]) -> None:
    """Set common fields on a BouncieTripMatch object from matched Bouncie trip data."""
    match.bouncie_trip_count = matched_bouncie.get("trip_count", 0)
    match.aggregated_distance_km = matched_bouncie.get("aggregated_distance_km")
    match.aggregated_distance_miles = matched_bouncie.get("aggregated_distance_miles")
    match.total_duration_hours = matched_bouncie.get("total_duration_hours")
    match.coordinates = matched_bouncie.get("coordinates")
    match.polyline = matched_bouncie.get("polyline")
    match.coordinate_count = matched_bouncie.get("coordinate_count", 0)
    match.bouncie_earliest_start = matched_bouncie.get("earliest_start")
    match.bouncie_latest_end = matched_bouncie.get("latest_end")
    match.match_data = serialized_match_data

# ------------------------------ AUTOMATIC PROCESSING ------------------------------

async def process_bouncie_link(
    db: Session,
    account_id: int,
    days_back: int = 365,
    skip_existing_matches: bool = True,
    force_rematch: bool = False
) -> Dict[str, Any]:
    """
    Automatically process Bouncie integration after linking:
    1. Fetch vehicles and create IMEI mappings
    2. Fetch recent trips
    3. Match with Turo trips (skipping already-matched trips by default)
    4. Store matches in database
    
    Args:
        db: Database session
        account_id: Account ID
        days_back: How many days back to fetch trips (default 60)
        skip_existing_matches: If True, skip trips that already have matches (default True)
        force_rematch: If True, re-match all trips even if matches exist (default False)
    
    Returns:
        Dict with processing results
    """
    try:
        try:
            account = get_account_or_raise(db, account_id)
        except HTTPException as e:
            return {"success": False, "error": e.detail}
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
        if not integration:
            return {"success": False, "error": "Bouncie not linked for this account"}
        
        service = BouncieService(db=db, account_id=account_id)
        
        # Ensure tokens are loaded and refresh if needed before making requests
        service._load_tokens()
        if not service.access_token:
            return {"success": False, "error": "No Bouncie access token available. Please reconnect Bouncie."}
        
        # Check if token is expired and refresh if possible
        if service.token_expires_at and service.token_expires_at < datetime.now(timezone.utc):
            if not service.refresh_token:
                return {"success": False, "error": "Bouncie token expired and no refresh token available. Please reconnect Bouncie."}
            logger.info(f"Token expired for account {account_id}, refreshing...")
            if not service._refresh_access_token_sync():
                return {"success": False, "error": "Bouncie token expired and refresh failed. Please reconnect Bouncie."}
        
        results = {
            "vehicles_mapped": 0,
            "trips_fetched": 0,
            "trips_matched": 0,
            "trips_skipped": 0,
            "matches_created": 0,
            "matches_updated": 0,
            "errors": []
        }

        logger.info(f"Fetching Bouncie vehicles for account {account_id}")
        vehicles_result = await service.get_vehicles()
        
        if not vehicles_result.get("success"):
            error_msg = f"Failed to fetch vehicles: {vehicles_result.get('error')}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return {"success": False, "results": results}
        
        bouncie_vehicles = vehicles_result.get("data", []) or []
        logger.info(f"Found {len(bouncie_vehicles)} Bouncie vehicle(s)")
        
        turo_vehicles = db.query(Vehicle).filter(Vehicle.account_id == account.id).all()
        
        for bv in bouncie_vehicles:
            imei = bv.get("imei")
            if not imei:
                continue
            
            existing = db.query(BouncieVehicleMapping).filter(
                BouncieVehicleMapping.account_id == account.id,
                BouncieVehicleMapping.imei == imei
            ).first()
            
            if not existing:
                turo_vehicle = None
                for tv in turo_vehicles:
                    existing_mapping = db.query(BouncieVehicleMapping).filter(
                        BouncieVehicleMapping.vehicle_id == tv.id
                    ).first()
                    if not existing_mapping:
                        turo_vehicle = tv
                        break
                
                if turo_vehicle:
                    mapping = BouncieVehicleMapping(
                        account_id=account.id,
                        vehicle_id=turo_vehicle.id,
                        imei=imei,
                        bouncie_nickname=bv.get("nickName"),
                        bouncie_vin=bv.get("vin")
                    )
                    db.add(mapping)
                    results["vehicles_mapped"] += 1
                    logger.info(f"Mapped Bouncie IMEI {imei} to Turo vehicle {turo_vehicle.id}")
        
        db.commit()
        
        logger.info(f"Fetching Bouncie trips for last {days_back} days")
        end_date = datetime.now()
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
        
        if not turo_trips:
            return {"success": True, "results": results, "message": "No Turo trips found to match"}
        
        trips_to_match = []
        if skip_existing_matches and not force_rematch:
            existing_match_trip_ids = {
                match.trip_id for match in db.query(BouncieTripMatch)
                .join(Trip, BouncieTripMatch.trip_id == Trip.id)
                .filter(Trip.account_id == account.id)
                .all()
            }
            
            for trip in turo_trips:
                if trip.id not in existing_match_trip_ids:
                    trips_to_match.append(trip)
                else:
                    results["trips_skipped"] += 1
            
            logger.info(
                f"Found {len(trips_to_match)} unmatched trips out of {len(turo_trips)} total trips. "
                f"Skipping {results['trips_skipped']} trips that already have matches."
            )
        else:
            trips_to_match = turo_trips
            if force_rematch:
                logger.info(f"Force re-matching enabled: will re-match all {len(trips_to_match)} trips")
        
        if not trips_to_match:
            return {
                "success": True,
                "results": results,
                "message": "All trips already have matches. Use force_rematch=True to re-match."
            }
        
        turo_trips_dict = [trip_to_dict(t) for t in trips_to_match]
        
        mappings = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        ).all()
        vehicle_imei_map = {mapping.vehicle_id: mapping.imei for mapping in mappings}
        
        logger.info(f"Matching {len(turo_trips_dict)} Turo trips with {len(all_bouncie_trips)} Bouncie trips")
        matches = match_all_trips(turo_trips_dict, all_bouncie_trips, vehicle_imei_map)
        
        results["trips_matched"] = len([m for m in matches if m.get("matched_bouncie_trip")])
        
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
            
            serialized_match_data = _serialize_datetime_for_json(matched_bouncie)
            
            if existing_match:
                _set_match_fields(existing_match, matched_bouncie, serialized_match_data)
                results["matches_updated"] += 1
            else:
                trip_match = BouncieTripMatch(
                    account_id=account.id,
                    trip_id=trip.id
                )
                _set_match_fields(trip_match, matched_bouncie, serialized_match_data)
                db.add(trip_match)
                results["matches_created"] += 1
        
        db.commit()
        
        logger.info(f"Successfully processed Bouncie link: {results}")
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.exception(f"Error processing Bouncie link: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}

async def handle_bouncie_auto_processing(db: Session, account_id: int) -> None:
    """Handle automatic Bouncie processing after OAuth callback (non-blocking)."""
    try:
        processing_result = await process_bouncie_link(db, account_id, days_back=365)
        if processing_result.get("success"):
            results = processing_result.get("results", {})
            logger.info(
                f"Auto-processing completed: "
                f"{results.get('vehicles_mapped')} vehicles mapped, "
                f"{results.get('trips_fetched')} trips fetched, "
                f"{results.get('matches_created')} matches created"
            )
        else:
            logger.warning(f"Auto-processing had issues: {processing_result.get('error')}")
    except Exception as e:
        logger.error(f"Error during auto-processing (non-fatal): {e}")

# ------------------------------ END OF FILE ------------------------------

