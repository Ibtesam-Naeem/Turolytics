# ------------------------------ IMPORTS ------------------------------
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .service import BouncieService
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_all_trips
from .utils import trip_to_dict
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

# ------------------------------ AUTOMATIC PROCESSING ------------------------------

async def process_bouncie_link(
    db: Session,
    account_id: int,
    days_back: int = 60,
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
        # Get account
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            account = DatabaseService.get_account_by_user_id(db, account_id)
        
        if not account:
            return {"success": False, "error": f"Account {account_id} not found"}
        
        # Check if Bouncie is linked
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
        if not integration:
            return {"success": False, "error": "Bouncie not linked for this account"}
        
        # Initialize service
        service = BouncieService(db=db, account_id=account_id)
        
        results = {
            "vehicles_mapped": 0,
            "trips_fetched": 0,
            "trips_matched": 0,
            "trips_skipped": 0,
            "matches_created": 0,
            "matches_updated": 0,
            "errors": []
        }
        
        # 1. Fetch and map vehicles
        logger.info(f"Fetching Bouncie vehicles for account {account_id}")
        vehicles_result = await service.get_vehicles()
        
        if not vehicles_result.get("success"):
            error_msg = f"Failed to fetch vehicles: {vehicles_result.get('error')}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return {"success": False, "results": results}
        
        bouncie_vehicles = vehicles_result.get("data", []) or []
        logger.info(f"Found {len(bouncie_vehicles)} Bouncie vehicle(s)")
        
        # Get Turo vehicles for this account
        turo_vehicles = db.query(Vehicle).filter(Vehicle.account_id == account.id).all()
        
        # Create vehicle mappings (simple: match by count or manual matching needed)
        # For now, we'll create mappings for all Bouncie vehicles
        # TODO: Add smarter matching logic (by VIN, license plate, etc.)
        for bv in bouncie_vehicles:
            imei = bv.get("imei")
            if not imei:
                continue
            
            # Check if mapping already exists
            existing = db.query(BouncieVehicleMapping).filter(
                BouncieVehicleMapping.account_id == account.id,
                BouncieVehicleMapping.imei == imei
            ).first()
            
            if not existing:
                # Try to match with Turo vehicle (simple: first unmatched vehicle)
                # In production, you'd want smarter matching
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
        
        # 2. Fetch recent trips
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
        
        # 3. Get Turo trips to match
        turo_trips = db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.status == "COMPLETED"
        ).all()
        
        if not turo_trips:
            return {"success": True, "results": results, "message": "No Turo trips found to match"}
        
        # 4. Filter out trips that already have matches (if skip_existing_matches is True)
        trips_to_match = []
        if skip_existing_matches and not force_rematch:
            # Get all existing matches for this account
            existing_match_trip_ids = set(
                db.query(BouncieTripMatch.trip_id)
                .join(Trip, BouncieTripMatch.trip_id == Trip.id)
                .filter(Trip.account_id == account.id)
                .all()
            )
            # Flatten the set of tuples to set of IDs
            existing_match_trip_ids = {trip_id[0] for trip_id in existing_match_trip_ids}
            
            # Filter trips - only include those without matches
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
        
        # Convert to dict format
        turo_trips_dict = [trip_to_dict(t) for t in trips_to_match]
        
        # Create IMEI map from vehicle mappings
        vehicle_imei_map = {}
        mappings = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        ).all()
        
        for mapping in mappings:
            # Map by vehicle_id
            vehicle_imei_map[mapping.vehicle_id] = mapping.imei
        
        # 5. Match trips (only unmatched ones)
        logger.info(f"Matching {len(turo_trips_dict)} Turo trips with {len(all_bouncie_trips)} Bouncie trips")
        matches = match_all_trips(turo_trips_dict, all_bouncie_trips, vehicle_imei_map)
        
        results["trips_matched"] = len([m for m in matches if m.get("matched_bouncie_trip")])
        
        # 6. Store matches in database
        for match in matches:
            turo_trip_dict = match.get("turo_trip")
            matched_bouncie = match.get("matched_bouncie_trip")
            
            if not matched_bouncie:
                continue
            
            # Find the Trip record
            trip = db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.trip_id == turo_trip_dict.get("trip_id")
            ).first()
            
            if not trip:
                continue
            
            # Check if match already exists
            existing_match = db.query(BouncieTripMatch).filter(
                BouncieTripMatch.trip_id == trip.id
            ).first()
            
            # Serialize match_data for JSON storage (convert datetime objects to strings)
            serialized_match_data = _serialize_datetime_for_json(matched_bouncie)
            
            if existing_match:
                # Update existing match
                existing_match.bouncie_trip_count = matched_bouncie.get("trip_count", 0)
                existing_match.aggregated_distance_km = matched_bouncie.get("aggregated_distance_km")
                existing_match.aggregated_distance_miles = matched_bouncie.get("aggregated_distance_miles")
                existing_match.total_duration_hours = matched_bouncie.get("total_duration_hours")
                existing_match.coordinates = matched_bouncie.get("coordinates")
                existing_match.polyline = matched_bouncie.get("polyline")
                existing_match.coordinate_count = matched_bouncie.get("coordinate_count", 0)
                existing_match.bouncie_earliest_start = matched_bouncie.get("earliest_start")
                existing_match.bouncie_latest_end = matched_bouncie.get("latest_end")
                existing_match.match_data = serialized_match_data
                results["matches_updated"] += 1
            else:
                # Create new match
                trip_match = BouncieTripMatch(
                    account_id=account.id,
                    trip_id=trip.id,
                    bouncie_trip_count=matched_bouncie.get("trip_count", 0),
                    aggregated_distance_km=matched_bouncie.get("aggregated_distance_km"),
                    aggregated_distance_miles=matched_bouncie.get("aggregated_distance_miles"),
                    total_duration_hours=matched_bouncie.get("total_duration_hours"),
                    coordinates=matched_bouncie.get("coordinates"),
                    polyline=matched_bouncie.get("polyline"),  # Stored polyline!
                    coordinate_count=matched_bouncie.get("coordinate_count", 0),
                    bouncie_earliest_start=matched_bouncie.get("earliest_start"),
                    bouncie_latest_end=matched_bouncie.get("latest_end"),
                    match_data=serialized_match_data
                )
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
        processing_result = await process_bouncie_link(db, account_id, days_back=60)
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

