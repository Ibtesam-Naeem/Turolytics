# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta

from .service import BouncieService, get_bouncie_vehicle_data
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_trip, match_all_trips
from .utils import trip_to_dict
from .schemas import (
    APIResponse,
    TokenExchangeRequest,
    MatchRequest,
    VehicleMappingRequest,
    BouncieTripMatchOut,
    BouncieTripMatchDetailOut,
    BouncieVehicleMappingOut,
)
from core.database import get_db
from core.database.models import Trip, BouncieTripMatch, BouncieVehicleMapping, Account, Vehicle
from core.database.db_service import DatabaseService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_bouncie_service(
    db: Session = Depends(get_db),
    account_id: Optional[int] = Query(None, description="Account ID")
) -> BouncieService:
    return BouncieService(db=db, account_id=account_id)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def check_result(result: Dict[str, Any], operation: str) -> APIResponse:
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Bouncie {operation} failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Bouncie {operation} failed: {error_msg}")
    return APIResponse(success=True, data=result.get("data", {}))

def _trip_to_dict(trip: Trip) -> Dict[str, Any]:
    """Convert Trip model to dict format for matching."""
    return {
        "trip_id": trip.trip_id,
        "vehicle_id": trip.vehicle_id,
        "start_date": trip.start_date,
        "start_time": trip.start_time,
        "end_date": trip.end_date,
        "end_time": trip.end_time,
        "kilometers_driven": trip.kilometers_driven,
        "status": trip.status,
        "scraped_at": trip.scraped_at.isoformat() if trip.scraped_at else None
    }

async def _fetch_turo_trips(
    db: Session,
    account_id: int,
    trip_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch Turo trips from database."""
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        account = DatabaseService.get_account_by_user_id(db, account_id)
        
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    
    if trip_id:
        trip = db.query(Trip).filter(
            Trip.account_id == account.id,
            Trip.trip_id == trip_id
        ).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        return [trip_to_dict(trip)]
    
    trips = db.query(Trip).filter(
        Trip.account_id == account.id,
        Trip.status == "COMPLETED"
    ).all()
    return [trip_to_dict(t) for t in trips]

async def _fetch_bouncie_trips(
    service: BouncieService,
    days_back: int,
    imei: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch Bouncie trips within the specified window while respecting API limits."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    trips = await fetch_trips_in_date_range(
        service=service,
        start_date=start_date,
        end_date=end_date,
        imei=imei
    )
    return trips

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.get("/auth/url", response_model=APIResponse, tags=["Authentication"])
async def get_authorization_url(
    account_id: int = Query(..., description="Account ID to associate with this auth"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get Bouncie OAuth authorization URL.
    The account_id is included in the state parameter so the callback knows which account to save tokens for.
    """
    state = str(account_id)
    url = service.get_authorization_url(state)
    return APIResponse(success=True, data={"authorization_url": url})

@router.post("/auth/token", response_model=APIResponse, tags=["Authentication"])
async def exchange_code_for_token(
    request: TokenExchangeRequest,
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Manually exchange authorization code for tokens (alternative to callback flow).
    Useful for testing or if you want to handle the callback differently.
    """
    if request.account_id:
        service.account_id = request.account_id
        
    result = await service.exchange_code_for_token(request.authorization_code)
    return check_result(result, "token exchange")

# ------------------------------ LIVE BOUNCIE API DATA ROUTES ------------------------------

@router.get("/data/vehicles", response_model=APIResponse, tags=["Live Data"])
async def get_vehicles(service: BouncieService = Depends(get_bouncie_service)):
    """Get vehicles from Bouncie API."""
    result = await service.get_vehicles()
    return check_result(result, "get vehicles")

@router.get("/data/vehicles/{imei}", response_model=APIResponse, tags=["Live Data"])
async def get_vehicle_by_imei(
    imei: str = Path(..., description="Bouncie device IMEI"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get specific vehicle by IMEI from Bouncie API."""
    result = await service.get_vehicle_by_imei(imei)
    return check_result(result, "get vehicle")

@router.get("/data/vehicles/{imei}/status", response_model=APIResponse, tags=["Live Data"])
async def get_vehicle_status(
    imei: str = Path(..., description="Bouncie device IMEI"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get current status of a vehicle from Bouncie API."""
    result = await service.get_current_vehicle_status(imei)
    return check_result(result, "get vehicle status")

@router.get("/data/vehicles/{imei}/analytics", response_model=APIResponse, tags=["Live Data"])
async def get_vehicle_analytics(
    imei: str = Path(..., description="Bouncie device IMEI"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get analytics for a vehicle from Bouncie API."""
    result = await service.get_vehicle_analytics(imei)
    return check_result(result, "get vehicle analytics")

@router.get("/data/trips", response_model=APIResponse, tags=["Live Data"])
async def get_trips(
    account_id: int = Query(..., description="Account ID"),
    gps_format: str = Query("geojson", description="GPS format (geojson)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    imei: Optional[str] = Query(None, description="Filter by IMEI"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get trips from Bouncie API. Changed from POST to GET with query parameters."""
    if service.account_id != account_id:
        service.account_id = account_id
        service._load_tokens()
    
    result = await service.get_trips(
        gps_format=gps_format,
        start_date=start_date,
        end_date=end_date,
        imei=imei
    )
    return check_result(result, "get trips")

@router.get("/data/trips/recent", response_model=APIResponse, tags=["Live Data"])
async def get_recent_trips(
    account_id: int = Query(..., description="Account ID"),
    days: int = Query(7, ge=1, le=30, description="Number of days back"),
    imei: Optional[str] = Query(None, description="Filter by IMEI"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get recent trips from Bouncie API."""
    if service.account_id != account_id:
        service.account_id = account_id
        service._load_tokens()
    
    result = await service.get_recent_trips(days, imei)
    return check_result(result, "get recent trips")

# ------------------------------ STORED MATCH DATA ROUTES ------------------------------

@router.get("/matches", response_model=APIResponse, tags=["Stored Data"])
async def get_stored_matches(
    account_id: int = Query(..., description="Account ID"),
    trip_id: Optional[str] = Query(None, description="Filter by Turo trip_id"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Get stored Bouncie trip matches from the database.
    Returns all matches for an account, optionally filtered by trip_id.
    """
    try:
        # Get account
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            account = DatabaseService.get_account_by_user_id(db, account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        
        # Build query
        query = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.account_id == account.id
        )
        
        # Filter by trip_id if provided
        if trip_id:
            trip = db.query(Trip).filter(
                Trip.account_id == account.id,
                Trip.trip_id == trip_id
            ).first()
            if not trip:
                return APIResponse(success=True, data={"matches": [], "total": 0, "limit": limit, "offset": offset})
            query = query.filter(BouncieTripMatch.trip_id == trip.id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        matches = query.offset(offset).limit(limit).all()
        
        # Format response
        matches_data = [
            BouncieTripMatchOut(
                id=match.id,
                trip_id=db.query(Trip).filter(Trip.id == match.trip_id).first().trip_id if db.query(Trip).filter(Trip.id == match.trip_id).first() else None,
                turo_trip_id=match.trip_id,
                bouncie_trip_count=match.bouncie_trip_count,
                aggregated_distance_km=match.aggregated_distance_km,
                aggregated_distance_miles=match.aggregated_distance_miles,
                total_duration_hours=match.total_duration_hours,
                coordinate_count=match.coordinate_count,
                has_polyline=bool(match.polyline),
                has_coordinates=bool(match.coordinates),
                has_match_data=bool(match.match_data),
                bouncie_earliest_start=match.bouncie_earliest_start,
                bouncie_latest_end=match.bouncie_latest_end,
                created_at=match.created_at,
                updated_at=match.updated_at,
            ).model_dump()
            for match in matches
        ]
        
        return APIResponse(
            success=True,
            data={
                "matches": matches_data,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving stored matches: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/matches/{match_id}", response_model=APIResponse, tags=["Stored Data"])
async def get_stored_match_detail(
    match_id: int = Path(..., description="Match ID"),
    account_id: int = Query(..., description="Account ID"),
    include_full_data: bool = Query(False, description="Include full coordinates and match_data"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific stored match.
    Optionally include full GPS coordinates and match_data (can be large).
    """
    try:
        # Get account
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            account = DatabaseService.get_account_by_user_id(db, account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        
        # Get match
        match = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.id == match_id,
            BouncieTripMatch.account_id == account.id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        trip = db.query(Trip).filter(Trip.id == match.trip_id).first()
        
        if include_full_data:
            match_out = BouncieTripMatchDetailOut(
                id=match.id,
                trip_id=trip.trip_id if trip else None,
                turo_trip_id=match.trip_id,
                bouncie_trip_count=match.bouncie_trip_count,
                aggregated_distance_km=match.aggregated_distance_km,
                aggregated_distance_miles=match.aggregated_distance_miles,
                total_duration_hours=match.total_duration_hours,
                coordinate_count=match.coordinate_count,
                has_polyline=bool(match.polyline),
                has_coordinates=bool(match.coordinates),
                has_match_data=bool(match.match_data),
                coordinates=match.coordinates,
                polyline=match.polyline,
                match_data=match.match_data,
                bouncie_earliest_start=match.bouncie_earliest_start,
                bouncie_latest_end=match.bouncie_latest_end,
                created_at=match.created_at,
                updated_at=match.updated_at,
            )
        else:
            match_out = BouncieTripMatchOut(
                id=match.id,
                trip_id=trip.trip_id if trip else None,
                turo_trip_id=match.trip_id,
                bouncie_trip_count=match.bouncie_trip_count,
                aggregated_distance_km=match.aggregated_distance_km,
                aggregated_distance_miles=match.aggregated_distance_miles,
                total_duration_hours=match.total_duration_hours,
                coordinate_count=match.coordinate_count,
                has_polyline=bool(match.polyline),
                has_coordinates=bool(match.coordinates),
                has_match_data=bool(match.match_data),
                bouncie_earliest_start=match.bouncie_earliest_start,
                bouncie_latest_end=match.bouncie_latest_end,
                created_at=match.created_at,
                updated_at=match.updated_at,
            )
        
        return APIResponse(success=True, data=match_out.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving match detail: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ VEHICLE MAPPING ROUTES ------------------------------

@router.get("/mappings", response_model=APIResponse, tags=["Stored Data"])
async def get_vehicle_mappings(
    account_id: int = Query(..., description="Account ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Get stored vehicle mappings (Turo vehicles linked to Bouncie IMEIs).
    Renamed from /vehicle-mappings to /mappings for consistency.
    """
    try:
        # Get account
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            account = DatabaseService.get_account_by_user_id(db, account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        
        # Build query
        query = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        mappings = query.offset(offset).limit(limit).all()
        
        mappings_data = []
        for mapping in mappings:
            vehicle = db.query(Vehicle).filter(Vehicle.id == mapping.vehicle_id).first()
            mappings_data.append(
                BouncieVehicleMappingOut(
                    id=mapping.id,
                    vehicle_id=mapping.vehicle_id,
                    vehicle_name=vehicle.name if vehicle else None,
                    imei=mapping.imei,
                    bouncie_nickname=mapping.bouncie_nickname,
                    bouncie_vin=mapping.bouncie_vin,
                    created_at=mapping.created_at,
                    updated_at=mapping.updated_at,
                ).model_dump()
            )
        
        return APIResponse(
            success=True,
            data={
                "mappings": mappings_data,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving vehicle mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
async def get_vehicle_mapping_detail(
    mapping_id: int = Path(..., description="Mapping ID"),
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db)
):
    """Get specific vehicle mapping by ID."""
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            account = DatabaseService.get_account_by_user_id(db, account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.id == mapping_id,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
        
        vehicle = db.query(Vehicle).filter(Vehicle.id == mapping.vehicle_id).first()
        
        mapping_out = BouncieVehicleMappingOut(
            id=mapping.id,
            vehicle_id=mapping.vehicle_id,
            vehicle_name=vehicle.name if vehicle else None,
            imei=mapping.imei,
            bouncie_nickname=mapping.bouncie_nickname,
            bouncie_vin=mapping.bouncie_vin,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )
        
        return APIResponse(success=True, data=mapping_out.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving mapping detail: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ ACTION ROUTES ------------------------------

@router.post("/matches/match", response_model=APIResponse, tags=["Actions"])
async def match_trips(
    request: MatchRequest,
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Real-time trip matching: Match Turo trips with Bouncie trips.
    Renamed from /match/trip to /matches/match for consistency.
    """
    try:
        if service.account_id != request.account_id:
            service.account_id = request.account_id
            service._load_tokens()
        elif not service.access_token:
            service._load_tokens()
            
        turo_trips = await _fetch_turo_trips(db, request.account_id, request.trip_id)
        if not turo_trips:
            return APIResponse(success=True, data={"matches": [], "message": "No trips found"})
        
        if request.authorization_code:
            token_result = await service.exchange_code_for_token(request.authorization_code)
            if not token_result.get("success"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Bouncie authentication failed: {token_result.get('error')}"
                )
        elif not service.access_token:
             raise HTTPException(status_code=401, detail="Bouncie authentication required (provide authorization_code or ensure saved token exists)")
        
        all_bouncie_trips = await _fetch_bouncie_trips(service, request.days_back, request.imei)
        if not all_bouncie_trips:
            return APIResponse(success=True, data={"matches": [], "message": "No Bouncie trips found"})
        
        if request.trip_id:
            turo_trip = turo_trips[0]
            match_result = match_trip(
                turo_trip,
                all_bouncie_trips,
                vehicle_imei=request.imei
            )
            
            return APIResponse(
                success=True,
                data={
                    "turo_trip": turo_trip,
                    "matched_bouncie_trip": match_result
                }
            )
        else:
            matches = match_all_trips(turo_trips, all_bouncie_trips)
            return APIResponse(success=True, data={"matches": matches})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error matching trips: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/matches/sync", response_model=APIResponse, tags=["Actions"])
async def sync_matches(
    account_id: int = Query(..., description="Account ID"),
    days_back: int = Query(60, ge=1, le=365, description="Number of days back to fetch"),
    skip_existing: bool = Query(True, description="Skip trips that already have matches"),
    force_rematch: bool = Query(False, description="Force re-matching of all trips (overrides skip_existing)"),
    db: Session = Depends(get_db)
):
    """
    Re-trigger automatic matching process.
    Fetches recent trips and matches them with Turo trips, storing results in database.
    
    By default, skips trips that already have matches for faster processing.
    Set force_rematch=True to re-match all trips.
    """
    try:
        from .auto_match import process_bouncie_link
        
        result = await process_bouncie_link(
            db,
            account_id,
            days_back=days_back,
            skip_existing_matches=skip_existing,
            force_rematch=force_rematch
        )
        
        if result.get("success"):
            return APIResponse(success=True, data=result.get("results", {}))
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Matching failed")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error syncing matches: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ WEBHOOK ROUTES ------------------------------

@router.get("/webhooks/events", response_model=APIResponse, tags=["Webhooks"])
async def get_webhook_events(service: BouncieService = Depends(get_bouncie_service)):
    """Get available webhook events."""
    events = service.get_webhook_events()
    return APIResponse(success=True, data={"events": events})

@router.post("/webhooks/validate", response_model=APIResponse, tags=["Webhooks"])
async def validate_webhook(
    payload: Dict[str, Any],
    service: BouncieService = Depends(get_bouncie_service)
):
    """Validate webhook payload."""
    is_valid = service.validate_webhook_payload(payload)
    return APIResponse(success=True, data={"valid": is_valid})

# ------------------------------ END OF FILE ------------------------------
