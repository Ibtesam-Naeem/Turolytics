# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path, Request
from typing import Optional, Dict, Any, List
import logging
import json
import asyncio
from datetime import datetime, timedelta, timezone

from .service import BouncieService
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_trip, match_all_trips
from .utils import trip_to_dict
from .helpers import format_date_for_api
from .schemas import (
    APIResponse,
    MatchRequest,
    VehicleMappingRequest,
    VehicleMappingUpdateRequest,
    BouncieTripMatchOut,
    BouncieTripMatchDetailOut,
    BouncieVehicleMappingOut,
    BouncieDTCCodeOut,
)
from core.database import get_db
from core.database.models import Trip, BouncieTripMatch, BouncieVehicleMapping, Account, Vehicle, BouncieDTCCode, BouncieWebhookLog, VehicleOdometerHistory
from core.security.auth import get_current_active_user
from core.utils.route_helpers import get_bouncie_integration, handle_route_errors
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_bouncie_service(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_active_user)
) -> BouncieService:
    return BouncieService(db=db, account=current_user)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def _build_match_out(match: BouncieTripMatch, trip: Trip = None, include_full_data: bool = False) -> BouncieTripMatchOut | BouncieTripMatchDetailOut:
    """Build BouncieTripMatchOut or BouncieTripMatchDetailOut from match and trip."""
    trip_id = trip.trip_id if trip else None
    base_data = {
        "id": match.id,
        "trip_id": trip_id,
        "turo_trip_id": match.trip_id,
        "bouncie_trip_count": match.bouncie_trip_count,
        "aggregated_distance_km": match.aggregated_distance_km,
        "aggregated_distance_miles": match.aggregated_distance_miles,
        "total_duration_hours": match.total_duration_hours,
        "coordinate_count": match.coordinate_count,
        "has_polyline": bool(match.polyline),
        "has_coordinates": bool(match.coordinates),
        "has_match_data": bool(match.match_data),
        "bouncie_earliest_start": match.bouncie_earliest_start,
        "bouncie_latest_end": match.bouncie_latest_end,
        "created_at": match.created_at,
        "updated_at": match.updated_at,
    }
    
    if include_full_data:
        return BouncieTripMatchDetailOut(**base_data, coordinates=match.coordinates, polyline=match.polyline, match_data=match.match_data)
    else:
        return BouncieTripMatchOut(**base_data)

async def _fetch_turo_trips(
    db: Session,
    current_user: Account,
    trip_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch Turo trips from database."""
    if trip_id:
        trip = db.query(Trip).filter(
            Trip.account_id == current_user.id,
            Trip.trip_id == trip_id
        ).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        return [trip_to_dict(trip)]
    
    trips = db.query(Trip).filter(
        Trip.account_id == current_user.id,
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
@handle_route_errors("getting authorization URL")
async def get_authorization_url(
    popup: bool = Query(False, description="Whether this is for a popup window (adds popup param to callback)"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get Bouncie OAuth authorization URL.
    The user_id is included in the state parameter so the callback knows which account to save tokens for.
    If popup=true, the callback will redirect to a popup-friendly page.
    """
    state = str(service.account.user_id)
    url = service.get_authorization_url(state)
    # Add popup parameter to state so callback knows it's a popup
    if popup:
        url += f"&popup=true"
    return APIResponse(success=True, data={"authorization_url": url})

@router.get("/auth/status", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("checking integration status")
async def get_integration_status(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if account has an active Bouncie integration.
    Returns integration status and basic info for authenticated user.
    """
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        return APIResponse(
            success=True,
            data={
                "connected": False,
                "message": "No Bouncie integration found for this account"
            }
        )
    
    is_expired = integration.expires_at < datetime.now(timezone.utc) if integration.expires_at else True
    
    return APIResponse(
        success=True,
        data={
            "connected": True,
            "expired": is_expired,
            "bouncie_user_id": integration.bouncie_user_id,
            "bouncie_user_email": integration.bouncie_user_email,
            "expires_at": integration.expires_at.isoformat() if integration.expires_at else None,
            "created_at": integration.created_at.isoformat() if integration.created_at else None,
            "updated_at": integration.updated_at.isoformat() if integration.updated_at else None
        }
    )

@router.delete("/auth/disconnect", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("disconnecting integration", rollback_db=True)
async def disconnect_integration(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Bouncie integration for authenticated user.
    Removes OAuth tokens and integration data from the database.
    """
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="No Bouncie integration found for this account"
        )

    db.delete(integration)
    db.commit()
    
    logger.info(f"Disconnected Bouncie integration for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "message": "Bouncie integration disconnected successfully",
            "account_id": current_user.id
        }
    )

@router.delete("/auth/delete-all-data", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("deleting all Bouncie data", rollback_db=True)
async def delete_all_bouncie_data(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete ALL Bouncie-related data for authenticated user.
    
    This is a comprehensive deletion endpoint for data privacy/GDPR compliance.
    Deletes:
    - All trip matches (BouncieTripMatch)
    - All vehicle mappings (BouncieVehicleMapping)
    - All DTC codes (BouncieDTCCode)
    - All webhook logs (BouncieWebhookLog)
    - Integration/OAuth tokens (BouncieIntegration)
    """
    deletion_summary = {
        "trip_matches_deleted": 0,
        "vehicle_mappings_deleted": 0,
        "dtc_codes_deleted": 0,
        "webhook_logs_deleted": 0,
        "integration_deleted": False
    }
    
    # Delete trip matches
    trip_matches = db.query(BouncieTripMatch).filter(
        BouncieTripMatch.account_id == current_user.id
    ).all()
    deletion_summary["trip_matches_deleted"] = len(trip_matches)
    for match in trip_matches:
        db.delete(match)
    
    # Delete vehicle mappings
    vehicle_mappings = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).all()
    deletion_summary["vehicle_mappings_deleted"] = len(vehicle_mappings)
    for mapping in vehicle_mappings:
        db.delete(mapping)
    
    # Delete DTC codes
    dtc_codes = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == current_user.id
    ).all()
    deletion_summary["dtc_codes_deleted"] = len(dtc_codes)
    for code in dtc_codes:
        db.delete(code)
    
    # Delete webhook logs
    webhook_logs = db.query(BouncieWebhookLog).filter(
        BouncieWebhookLog.account_id == current_user.id
    ).all()
    deletion_summary["webhook_logs_deleted"] = len(webhook_logs)
    for log in webhook_logs:
        db.delete(log)
    
    # Delete integration
    integration = get_bouncie_integration(db, current_user.id)
    if integration:
        db.delete(integration)
        deletion_summary["integration_deleted"] = True
    
    db.commit()
    
    logger.info(
        f"Deleted all Bouncie data for account {current_user.id}: "
        f"{deletion_summary['trip_matches_deleted']} trip matches, "
        f"{deletion_summary['vehicle_mappings_deleted']} vehicle mappings, "
        f"{deletion_summary['dtc_codes_deleted']} DTC codes, "
        f"{deletion_summary['webhook_logs_deleted']} webhook logs, "
        f"integration: {deletion_summary['integration_deleted']}"
    )
    
    return APIResponse(
        success=True,
        data={
            "message": "All Bouncie data deleted successfully",
            "account_id": current_user.id,
            "deletion_summary": deletion_summary
        }
    )

@router.get("/auth/token", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("getting access token")
async def get_access_token(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get access token for frontend to use directly with Bouncie API.
    Returns temporary access token that frontend can use to call Bouncie API directly.
    """
    logger.debug(f"Token request from user {current_user.id}")
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        logger.warning(f"No Bouncie integration found for user {current_user.id}")
        raise HTTPException(
            status_code=404,
            detail="Bouncie not connected for this account"
        )
    
    service = BouncieService(db=db, account=current_user)
    
    if integration.expires_at and integration.expires_at < datetime.now(timezone.utc):
        logger.info(f"Token expired for account {current_user.id}, refreshing")
        refresh_success = await asyncio.to_thread(service._refresh_access_token)
        if not refresh_success:
            logger.error(f"Token refresh failed for account {current_user.id}")
            raise HTTPException(
                status_code=401,
                detail="Token expired and refresh failed. Please reconnect Bouncie."
            )
    
    service._load_tokens()
    
    if not service.access_token:
        logger.error(f"No access token available for account {current_user.id}")
        raise HTTPException(
            status_code=401,
            detail="No access token available. Please reconnect Bouncie."
        )
    
    expires_in = 3600
    if integration.expires_at:
        expires_in = int((integration.expires_at - datetime.now(timezone.utc)).total_seconds())
        expires_in = max(0, expires_in)
    
    logger.debug(f"Token provided to user {current_user.id}, expires in {expires_in}s")
    return APIResponse(
        success=True,
        data={
            "access_token": service.access_token,
            "expires_in": expires_in,
            "token_type": "Bearer"
        }
    )

# ------------------------------ STORED MATCH DATA ROUTES ------------------------------

@router.get("/matches", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving stored matches")
async def get_stored_matches(
    trip_id: Optional[str] = Query(None, description="Filter by Turo trip_id"),
    include_polylines: bool = Query(False, description="Include polyline and coordinate data for map display"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get stored Bouncie trip matches from the database.
    Returns all matches for authenticated user, optionally filtered by trip_id.
    """
    query = db.query(BouncieTripMatch).filter(
        BouncieTripMatch.account_id == current_user.id
    )
    
    if trip_id:
        trip = db.query(Trip).filter(
            Trip.account_id == current_user.id,
            Trip.trip_id == trip_id
        ).first()
        if not trip:
            return APIResponse(success=True, data={"matches": [], "total": 0, "limit": limit, "offset": offset})
        query = query.filter(BouncieTripMatch.trip_id == trip.id)
    
    total = query.count()
    
    matches = query.offset(offset).limit(limit).all()
    
    trip_ids = [match.trip_id for match in matches]
    trips_dict = {trip.id: trip for trip in db.query(Trip).filter(Trip.id.in_(trip_ids)).all()}
    
    matches_data = [
        _build_match_out(match, trips_dict.get(match.trip_id), include_full_data=include_polylines).model_dump()
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

@router.get("/matches/{match_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving match detail")
async def get_stored_match_detail(
    match_id: int = Path(..., description="Match ID"),
    include_full_data: bool = Query(False, description="Include full coordinates and match_data"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific stored match."""
    match = db.query(BouncieTripMatch).filter(
        BouncieTripMatch.id == match_id,
        BouncieTripMatch.account_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    
    trip = db.query(Trip).filter(Trip.id == match.trip_id).first()
    match_out = _build_match_out(match, trip, include_full_data=include_full_data)
    
    return APIResponse(success=True, data=match_out.model_dump())

# ------------------------------ VEHICLE MAPPING ROUTES ------------------------------

@router.get("/mappings", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving vehicle mappings")
async def get_vehicle_mappings(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored vehicle mappings (Turo vehicles linked to Bouncie IMEIs)."""
    query = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    )
    
    total = query.count()
    
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

@router.get("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("retrieving mapping detail")
async def get_vehicle_mapping_detail(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific vehicle mapping by ID."""
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
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

@router.post("/mappings", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("creating vehicle mapping", rollback_db=True)
async def create_vehicle_mapping(
    request: VehicleMappingRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle mapping (link Turo vehicle to Bouncie IMEI).
    """
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == request.vehicle_id,
        Vehicle.account_id == current_user.id
    ).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle {request.vehicle_id} not found for this account"
        )
    
    existing_mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.vehicle_id == request.vehicle_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if existing_mapping:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping (ID: {existing_mapping.id})"
        )
    
    existing_imei = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.imei == request.imei,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if existing_imei:
        raise HTTPException(
            status_code=400,
            detail=f"IMEI {request.imei} is already mapped to vehicle {existing_imei.vehicle_id}"
        )
    
    mapping = BouncieVehicleMapping(
        account_id=current_user.id,
        vehicle_id=request.vehicle_id,
        imei=request.imei,
        bouncie_nickname=request.bouncie_nickname,
        bouncie_vin=request.bouncie_vin
    )
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    mapping_out = BouncieVehicleMappingOut(
        id=mapping.id,
        vehicle_id=mapping.vehicle_id,
        vehicle_name=vehicle.name,
        imei=mapping.imei,
        bouncie_nickname=mapping.bouncie_nickname,
        bouncie_vin=mapping.bouncie_vin,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )
    
    logger.info(f"Created vehicle mapping: vehicle_id={request.vehicle_id}, imei={request.imei}")
    
    return APIResponse(
        success=True,
        data={
            "mapping": mapping_out.model_dump(),
            "message": "Vehicle mapping created successfully"
        }
    )

@router.put("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("updating vehicle mapping", rollback_db=True)
async def update_vehicle_mapping(
    mapping_id: int = Path(..., description="Mapping ID"),
    request: VehicleMappingUpdateRequest = ...,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing vehicle mapping.
    Only provided fields will be updated.
    """
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    
    if request.vehicle_id is not None and request.vehicle_id != mapping.vehicle_id:
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == request.vehicle_id,
            Vehicle.account_id == current_user.id
        ).first()
        
        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle {request.vehicle_id} not found for this account"
            )
        
        existing_mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.vehicle_id == request.vehicle_id,
            BouncieVehicleMapping.account_id == current_user.id,
            BouncieVehicleMapping.id != mapping_id
        ).first()
        
        if existing_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping (ID: {existing_mapping.id})"
            )
        
        mapping.vehicle_id = request.vehicle_id
    
    if request.imei is not None and request.imei != mapping.imei:
        existing_imei = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.imei == request.imei,
            BouncieVehicleMapping.account_id == current_user.id,
            BouncieVehicleMapping.id != mapping_id
        ).first()
        
        if existing_imei:
            raise HTTPException(
                status_code=400,
                detail=f"IMEI {request.imei} is already mapped to vehicle {existing_imei.vehicle_id}"
            )
        
        mapping.imei = request.imei
    
    if request.bouncie_nickname is not None:
        mapping.bouncie_nickname = request.bouncie_nickname
    
    if request.bouncie_vin is not None:
        mapping.bouncie_vin = request.bouncie_vin
    
    db.commit()
    db.refresh(mapping)
    
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
    
    logger.info(f"Updated vehicle mapping {mapping_id}")
    
    return APIResponse(
        success=True,
        data={
            "mapping": mapping_out.model_dump(),
            "message": "Vehicle mapping updated successfully"
        }
    )

@router.delete("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
@handle_route_errors("deleting vehicle mapping", rollback_db=True)
async def delete_vehicle_mapping(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a vehicle mapping.
    This will unlink the Turo vehicle from the Bouncie IMEI.
    """
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.id == mapping_id,
        BouncieVehicleMapping.account_id == current_user.id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    
    vehicle_id = mapping.vehicle_id
    imei = mapping.imei
    
    db.delete(mapping)
    db.commit()
    
    logger.info(f"Deleted vehicle mapping {mapping_id} (vehicle_id={vehicle_id}, imei={imei})")
    
    return APIResponse(
        success=True,
        data={
            "message": f"Vehicle mapping {mapping_id} deleted successfully",
            "deleted_mapping": {
                "id": mapping_id,
                "vehicle_id": vehicle_id,
                "imei": imei
            }
        }
    )

# ------------------------------ ACTION ROUTES ------------------------------

@router.post("/matches/match", response_model=APIResponse, tags=["Actions"])
@handle_route_errors("matching trips")
async def match_trips(
    request: MatchRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Real-time trip matching: Match Turo trips with Bouncie trips."""
    if not service.access_token:
        service._load_tokens()
        
    turo_trips = await _fetch_turo_trips(db, current_user, request.trip_id)
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

@router.post("/matches/sync", response_model=APIResponse, tags=["Actions"])
@handle_route_errors("syncing matches")
async def sync_matches(
    days_back: int = Query(365, ge=1, le=365, description="Number of days back to fetch"),
    skip_existing: bool = Query(True, description="Skip trips that already have matches"),
    force_rematch: bool = Query(False, description="Force re-matching of all trips (overrides skip_existing)"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Re-trigger automatic matching process. Fetches recent trips and matches them with Turo trips, storing results in database. By default, skips trips that already have matches for faster processing. Set force_rematch=True to re-match all trips."""
    from .auto_match import process_bouncie_link
    
    result = await process_bouncie_link(
        db,
        current_user.id,
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

# ------------------------------ LIVE DATA PROXY ROUTES ------------------------------
# These routes proxy Bouncie API calls to avoid CORS issues from frontend

@router.get("/vehicles", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("fetching vehicles")
async def get_vehicles_proxy(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get all vehicles from Bouncie with their current status.
    This is a proxy route to avoid CORS issues when calling Bouncie API from frontend.
    """
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )
    
    result = await service.get_vehicles()
    
    if result.get("success"):
        return APIResponse(
            success=True,
            data={"vehicles": result.get("data", [])}
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vehicles: {result.get('error')}"
        )

@router.get("/trips", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("fetching trips")
async def get_trips_proxy(
    imei: Optional[str] = Query(None, description="Filter by IMEI (required by Bouncie API)"),
    gps_format: str = Query("geojson", description="GPS format"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get trips from Bouncie.
    This is a proxy route to avoid CORS issues when calling Bouncie API from frontend.
    Note: Bouncie API requires IMEI parameter.
    """
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )
    
    if not imei:
        raise HTTPException(
            status_code=400,
            detail="IMEI parameter is required by Bouncie API"
        )
    
    result = await service.get_trips(
        gps_format=gps_format,
        start_date=start_date,
        end_date=end_date,
        imei=imei
    )
    
    if result.get("success"):
        return APIResponse(
            success=True,
            data=result.get("data", [])
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trips: {result.get('error')}"
        )

@router.get("/live", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("fetching live vehicle data")
async def get_live_vehicles(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get aggregated live vehicle data with location, speed, fuel, and trip information.
    This endpoint processes Bouncie data similar to the test script and returns
    a clean structure optimized for frontend map display.
    """
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )
    
    # Get all vehicles from Bouncie
    vehicles_result = await service.get_vehicles()
    if not vehicles_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vehicles: {vehicles_result.get('error')}"
        )
    
    vehicles = vehicles_result.get("data", [])
    if not vehicles:
        return APIResponse(success=True, data={"vehicles": []})
    
    # Get vehicle mappings to link IMEI to vehicle_id
    mappings = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).all()
    imei_to_vehicle_id = {mapping.imei: mapping.vehicle_id for mapping in mappings}
    
    # Get today's date for trips
    today = datetime.now()
    today_str = format_date_for_api(today.replace(hour=0, minute=0, second=0, microsecond=0))
    
    # Process each vehicle
    live_vehicles = []
    
    for vehicle in vehicles:
        imei = vehicle.get('imei')
        if not imei:
            continue
        
        # Get vehicle_id from mapping - only process vehicles that are mapped
        vehicle_id = imei_to_vehicle_id.get(imei)
        if not vehicle_id:
            # Skip vehicles without mappings (not linked to Turo vehicles)
            continue
        
        # Extract location from stats.location (as shown in test script)
        location = None
        stats = vehicle.get('stats')
        if isinstance(stats, dict) and stats.get('location'):
            stats_location = stats.get('location')
            if isinstance(stats_location, dict):
                lat = stats_location.get('lat')
                lon = stats_location.get('lon')
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    location = {"lat": float(lat), "lon": float(lon)}
        
        # If no location in stats, try vehicle.location (fallback)
        if not location and vehicle.get('location'):
            vehicle_location = vehicle.get('location')
            if isinstance(vehicle_location, dict):
                lat = vehicle_location.get('lat')
                lon = vehicle_location.get('lon')
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    location = {"lat": float(lat), "lon": float(lon)}
        
        # Skip vehicles without location (no active tracker)
        if not location:
            continue
        
        # Get today's trips for this vehicle
        trips_result = await service.get_trips(
            gps_format="geojson",
            start_date=today_str,
            end_date=format_date_for_api(today),
            imei=imei
        )
        
        trips_today = trips_result.get("data", []) if trips_result.get("success") else []
        
        # Calculate miles driven today
        miles_driven_today = sum(trip.get('distance', 0) or 0 for trip in trips_today)
        
        # Find active trip (no endTime)
        active_trip = next((trip for trip in trips_today if not trip.get('endTime')), None)
        
        # Extract location from active trip GPS if available (most recent)
        if active_trip and active_trip.get('gps'):
            gps = active_trip.get('gps')
            if isinstance(gps, dict) and gps.get('coordinates'):
                coords = gps.get('coordinates')
                if isinstance(coords, list) and len(coords) > 0:
                    last_coord = coords[-1]
                    if isinstance(last_coord, list) and len(last_coord) >= 2:
                        # GeoJSON format is [lon, lat]
                        location = {"lat": float(last_coord[1]), "lon": float(last_coord[0])}
        
        # Extract other vehicle data
        speed = 0
        if active_trip and active_trip.get('speed'):
            speed = active_trip.get('speed')
        elif isinstance(stats, dict) and stats.get('speed'):
            speed = stats.get('speed')
        elif vehicle.get('speed'):
            speed = vehicle.get('speed')
        
        fuel_level = None
        if isinstance(stats, dict):
            fuel_level = stats.get('fuelLevel') or stats.get('fuel')
        if not fuel_level:
            fuel_level = vehicle.get('fuelLevel') or vehicle.get('fuel')
        
        # Determine status
        status = "parked"
        if active_trip:
            status = "moving"
        elif isinstance(stats, dict) and stats.get('isRunning'):
            status = "moving"
        elif vehicle.get('status') == "offline":
            status = "offline"
        
        # Extract flags/metrics
        flags = {}
        if active_trip:
            flags = {
                "rapidAcceleration": active_trip.get('rapidAcceleration') or active_trip.get('rapidAccel') or 0,
                "hardBraking": active_trip.get('hardBraking') or active_trip.get('hardBrake') or 0,
            }
        
        # Extract MIL (Malfunction Indicator Lamp) / Check Engine Light from stats
        engine_light = False
        if isinstance(stats, dict):
            engine_light = stats.get('mil') or stats.get('checkEngine') or False
        
        # Also check vehicle level (fallback)
        if not engine_light:
            engine_light = vehicle.get('mil') or vehicle.get('checkEngine') or False
        
        # Add engine_light to flags
        flags['engineLight'] = engine_light
        
        live_vehicle = {
            "vehicleId": vehicle_id,
            "imei": imei,
            "vehicleName": vehicle.get('nickName') or vehicle.get('nickname') or f"Vehicle {imei}",
            "location": location,
            "status": status,
            "speed": float(speed) if speed else 0,
            "fuelLevel": float(fuel_level) if fuel_level is not None else None,
            "batteryLevel": (stats.get('battery') if isinstance(stats, dict) else None) or vehicle.get('batteryLevel') or vehicle.get('battery'),
            "milesDrivenToday": float(miles_driven_today),
            "activeTrip": active_trip,
            "flags": flags,
            # Add engine info if available
            "engineInfo": vehicle.get('standardEngine'),
            "odometer": stats.get('odometer') if isinstance(stats, dict) else None,
        }
        
        live_vehicles.append(live_vehicle)
    
    return APIResponse(
        success=True,
        data={"vehicles": live_vehicles}
    )

# ------------------------------ ODOMETER ROUTES ------------------------------

@router.get("/odometer/{imei}", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("getting odometer at timestamp")
async def get_odometer_at_time(
    imei: str = Path(..., description="Vehicle IMEI"),
    timestamp: str = Query(..., description="ISO timestamp (e.g., 2025-12-27T01:00:00 or 2025-12-27T01:00:00Z)"),
    days_buffer: int = Query(1, description="Days before/after to fetch trips", ge=1, le=7),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get odometer reading at a specific timestamp using Bouncie trips.
    
    The function will:
    1. Fetch trips around the target timestamp
    2. Find the trip that contains the timestamp (if any)
    3. Return the odometer reading (interpolated if within a trip)
    4. If no trip contains the timestamp, return the odometer from the nearest trip
    """
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )
    
    # Parse timestamp
    try:
        # Handle both with and without timezone
        target_time = timestamp.replace('Z', '+00:00')
        target_time = datetime.fromisoformat(target_time)
        # Remove timezone for consistency
        if target_time.tzinfo:
            target_time = target_time.replace(tzinfo=None)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timestamp format. Use ISO format (e.g., 2025-12-27T01:00:00). Error: {str(e)}"
        )
    
    # Fetch trips around target time
    start_date = target_time - timedelta(days=days_buffer)
    end_date = target_time + timedelta(days=days_buffer)
    
    trips_result = await service.get_trips(
        start_date=format_date_for_api(start_date),
        end_date=format_date_for_api(end_date),
        imei=imei
    )
    
    if not trips_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trips from Bouncie: {trips_result.get('error', 'Unknown error')}"
        )
    
    trips = trips_result.get("data", [])
    
    # Get odometer from trips
    from .helpers import get_odometer_at_time_from_trips
    result = get_odometer_at_time_from_trips(trips, target_time, imei=imei)
    
    if result:
        return APIResponse(success=True, data=result)
    else:
        return APIResponse(
            success=False,
            data={
                "message": f"No odometer data found for IMEI {imei} at timestamp {timestamp}",
                "timestamp": timestamp,
                "imei": imei,
                "trips_found": len(trips)
            }
        )

# ------------------------------ ODOMETER SNAPSHOT ROUTES ------------------------------

@router.post("/odometer/snapshot", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("storing odometer snapshot")
async def store_odometer_snapshot(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Store daily odometer snapshots for all mapped vehicles.
    This should be called once daily (via cron job or scheduled task).
    Gets current odometer from Bouncie and stores it in VehicleOdometerHistory.
    """
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )
    
    # Get all vehicle mappings for this account
    mappings = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).all()
    
    if not mappings:
        return APIResponse(
            success=True,
            data={
                "message": "No vehicle mappings found",
                "snapshots_stored": 0
            }
        )
    
    # Get all vehicles from Bouncie
    vehicles_result = await service.get_vehicles()
    if not vehicles_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vehicles from Bouncie: {vehicles_result.get('error')}"
        )
    
    bouncie_vehicles = vehicles_result.get("data", []) or []
    imei_to_vehicle = {v.get("imei"): v for v in bouncie_vehicles if v.get("imei")}
    
    # Today's date (date only, no time)
    today = datetime.now().date()
    today_datetime = datetime.combine(today, datetime.min.time())
    
    snapshots_stored = 0
    snapshots_updated = 0
    errors = []
    
    for mapping in mappings:
        try:
            imei = mapping.imei
            vehicle_id = mapping.vehicle_id
            
            # Get vehicle data from Bouncie
            bouncie_vehicle = imei_to_vehicle.get(imei)
            if not bouncie_vehicle:
                errors.append(f"Vehicle with IMEI {imei} not found in Bouncie")
                continue
            
            # Get odometer from stats
            stats = bouncie_vehicle.get('stats', {})
            odometer_miles = None
            
            if isinstance(stats, dict):
                odometer_miles = stats.get('odometer')
            
            # Fallback: try vehicle level
            if odometer_miles is None:
                odometer_miles = bouncie_vehicle.get('odometer')
            
            if odometer_miles is None:
                errors.append(f"No odometer data for IMEI {imei}")
                continue
            
            # Check if snapshot already exists for today
            existing = db.query(VehicleOdometerHistory).filter(
                VehicleOdometerHistory.vehicle_id == vehicle_id,
                VehicleOdometerHistory.account_id == current_user.id,
                func.date(VehicleOdometerHistory.date) == today
            ).first()
            
            if existing:
                # Update existing snapshot
                existing.odometer_miles = float(odometer_miles)
                existing.recorded_at = datetime.now(timezone.utc)
                snapshots_updated += 1
            else:
                # Create new snapshot
                snapshot = VehicleOdometerHistory(
                    vehicle_id=vehicle_id,
                    account_id=current_user.id,
                    imei=imei,
                    odometer_miles=float(odometer_miles),
                    date=today_datetime,
                    source="bouncie",
                    recorded_at=datetime.now(timezone.utc)
                )
                db.add(snapshot)
                snapshots_stored += 1
            
        except Exception as e:
            logger.error(f"Error storing odometer snapshot for vehicle {mapping.vehicle_id}: {e}")
            errors.append(f"Vehicle {mapping.vehicle_id}: {str(e)}")
    
    db.commit()
    
    return APIResponse(
        success=True,
        data={
            "message": "Odometer snapshots stored",
            "snapshots_stored": snapshots_stored,
            "snapshots_updated": snapshots_updated,
            "total_processed": len(mappings),
            "errors": errors if errors else None
        }
    )

# ------------------------------ WEBHOOK ROUTES ------------------------------

@router.get("/webhooks/events", response_model=APIResponse, tags=["Webhooks"])
@handle_route_errors("getting webhook events")
async def get_webhook_events(service: BouncieService = Depends(get_bouncie_service)):
    """Get available webhook events."""
    events = service.get_webhook_events()
    return APIResponse(success=True, data={"events": events})

@router.get("/webhooks/url", response_model=APIResponse, tags=["Webhooks"])
@handle_route_errors("getting webhook URL")
async def get_webhook_url(
    current_user: Account = Depends(get_current_active_user)
):
    """
    Get the webhook URL that should be registered with Bouncie.
    Users need to register this URL in their Bouncie developer dashboard.
    """
    import os
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    webhook_url = f"{backend_url}/api/bouncie/webhooks/bouncie"
    
    return APIResponse(
        success=True,
        data={
            "webhook_url": webhook_url,
            "instructions": "Register this URL in your Bouncie developer dashboard to receive webhook events. Make sure your backend is publicly accessible (HTTPS required for production)."
        }
    )

def _verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify Bouncie webhook signature.
    Bouncie uses HMAC-SHA256 to sign webhooks.
    
    Args:
        payload: Raw request body as string
        signature: Signature from X-Bouncie-Signature header
        secret: Webhook secret from Bouncie
    
    Returns:
        True if signature is valid, False otherwise
    """
    import hmac
    import hashlib
    
    if not signature or not secret:
        return False
    
    try:
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

@router.post("/webhooks/bouncie", tags=["Webhooks"])
@handle_route_errors("processing Bouncie webhook", rollback_db=False)
async def handle_bouncie_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle incoming webhooks from Bouncie.
    This endpoint receives POST requests directly from Bouncie's servers.
    
    Expected payload structure (varies by event type):
    {
        "event": "new_mil_event",
        "imei": "device_imei",
        "timestamp": "2025-01-01T12:00:00Z",
        "data": {
            "code": "P0301",
            "description": "Cylinder 1 Misfire Detected",
            ...
        }
    }
    """
    import os
    from datetime import datetime
    
    # Get raw body for signature verification
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')
    
    # Parse JSON payload
    try:
        payload = json.loads(body_str)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        webhook_log = BouncieWebhookLog(
            event_type="unknown",
            raw_payload={},
            processed=False,
            error_message=f"Invalid JSON payload: {str(e)}",
            signature_valid=None
        )
        db.add(webhook_log)
        db.commit()
        return {"status": "error", "message": "Invalid JSON payload"}
    
    # Verify webhook signature (if secret is configured)
    webhook_secret = os.getenv("BOUNCIE_WEBHOOK_SECRET")
    signature = request.headers.get("X-Bouncie-Signature") or request.headers.get("X-Signature")
    signature_valid = None
    
    if webhook_secret and signature:
        signature_valid = _verify_webhook_signature(body_str, signature, webhook_secret)
        if not signature_valid:
            logger.warning("Webhook signature verification failed - possible security issue")
            webhook_log = BouncieWebhookLog(
                event_type=payload.get("event", "unknown"),
                imei=payload.get("imei"),
                raw_payload=payload,
                headers=dict(request.headers),
                processed=False,
                error_message="Invalid webhook signature",
                signature_valid=False
            )
            db.add(webhook_log)
            db.commit()
            return {"status": "error", "message": "Invalid signature"}, 401
    elif webhook_secret and not signature:
        logger.warning("Webhook secret configured but no signature provided")
        signature_valid = False
    else:
        logger.info("Webhook signature verification skipped (no secret configured)")
        signature_valid = None
    
    logger.info("=" * 80)
    logger.info("BOUNCIE WEBHOOK RECEIVED")
    logger.info(f"Event: {payload.get('event')}")
    logger.info(f"IMEI: {payload.get('imei')}")
    logger.info(f"Signature valid: {signature_valid}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    logger.info("=" * 80)
    
    event_type = payload.get("event") or payload.get("type")
    if not event_type:
        logger.warning("Webhook received without event type")
        webhook_log = BouncieWebhookLog(
            event_type="unknown",
            raw_payload=payload,
            headers=dict(request.headers),
            processed=False,
            error_message="Missing event type",
            signature_valid=signature_valid
        )
        db.add(webhook_log)
        db.commit()
        return {"status": "error", "message": "Missing event type"}
    
    imei = payload.get("imei") or payload.get("device_imei") or payload.get("data", {}).get("imei")
    
    # Find account(s) that have this IMEI mapped
    account_id = None
    vehicle_id = None
    if imei:
        mappings = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.imei == imei
        ).all()
        if mappings:
            # Use first mapping (most common case)
            mapping = mappings[0]
            account_id = mapping.account_id
            vehicle_id = mapping.vehicle_id
        else:
            logger.warning(f"No vehicle mapping found for IMEI {imei} - webhook logged but not processed")
    else:
        logger.warning("Webhook received without IMEI")
    
    # Log webhook event
    webhook_log = BouncieWebhookLog(
        account_id=account_id,
        vehicle_id=vehicle_id,
        event_type=event_type,
        imei=imei,
        raw_payload=payload,
        headers=dict(request.headers),
        processed=False,
        signature_valid=signature_valid
    )
    db.add(webhook_log)
    db.flush()  # Flush to get the ID
    
    # Process webhook based on event type
    try:
        if event_type == "new_mil_event":
            if account_id and vehicle_id:
                await _handle_mil_event(db, account_id, vehicle_id, imei, payload)
        elif event_type == "trip_ended":
            if account_id and vehicle_id:
                await _handle_trip_ended(db, account_id, vehicle_id, imei, payload)
        elif event_type == "device_connected":
            if account_id and vehicle_id:
                await _handle_device_connected(db, account_id, vehicle_id, imei, payload)
        elif event_type == "device_disconnected":
            if account_id and vehicle_id:
                await _handle_device_disconnected(db, account_id, vehicle_id, imei, payload)
        elif event_type == "vin_change":
            if account_id and vehicle_id:
                await _handle_vin_change(db, account_id, vehicle_id, imei, payload)
        elif event_type == "new_trip_data":
            logger.info(f"New trip data for device {imei}, account {account_id}")
        elif event_type == "new_battery_status":
            logger.info(f"Battery status update for device {imei}, account {account_id}")
        else:
            logger.info(f"Unhandled webhook event type: {event_type} for IMEI {imei}")
        
        # Mark as processed
        webhook_log.processed = True
        db.commit()
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        webhook_log.processed = False
        webhook_log.error_message = str(e)
        db.commit()
        # Still return 200 to prevent Bouncie from retrying immediately
        return {"status": "error", "message": "Processing failed but logged"}
    
    # Always return 200 OK to acknowledge receipt
    return {"status": "ok", "message": "Webhook processed"}

async def _handle_mil_event(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle new_mil_event webhook - store DTC codes."""
    from datetime import datetime, timezone
    
    logger.info(f"Processing MIL event for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    # Extract DTC code information from payload
    # Bouncie payload structure may vary, so we check multiple possible locations
    data = payload.get("data", {})
    
    # Try to extract code from various possible locations
    dtc_code = (
        data.get("code") or 
        data.get("dtc") or 
        data.get("dtc_code") or
        payload.get("code") or
        payload.get("dtc")
    )
    
    if not dtc_code:
        logger.warning(f"No DTC code found in MIL event payload: {payload}")
        return
    
    # Extract description
    description = (
        data.get("description") or 
        data.get("message") or
        payload.get("description") or
        payload.get("message")
    )
    
    # Extract timestamp
    timestamp_str = (
        payload.get("timestamp") or 
        payload.get("time") or
        data.get("timestamp") or
        data.get("time")
    )
    
    if timestamp_str:
        try:
            # Try parsing ISO format timestamp
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            occurred_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if occurred_at.tzinfo is None:
                occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
            occurred_at = datetime.now(timezone.utc)
    else:
        occurred_at = datetime.now(timezone.utc)
    
    # Check if this code already exists and is active
    existing_code = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == account_id,
        BouncieDTCCode.imei == imei,
        BouncieDTCCode.code == dtc_code,
        BouncieDTCCode.is_active == True
    ).first()
    
    if existing_code:
        logger.info(f"DTC code {dtc_code} already exists and is active for IMEI {imei}")
        return
    
    # Create new DTC code record
    dtc_record = BouncieDTCCode(
        account_id=account_id,
        vehicle_id=vehicle_id,
        imei=imei,
        code=dtc_code,
        description=description,
        is_active=True,
        occurred_at=occurred_at,
        raw_data=json.dumps(payload)  # Store raw payload for debugging
    )
    
    db.add(dtc_record)
    db.commit()
    db.refresh(dtc_record)
    
    logger.info(f"Stored new DTC code: {dtc_code} ({description}) for IMEI {imei}, vehicle {vehicle_id}")
    
    return dtc_record

async def _handle_trip_ended(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle trip_ended webhook - trigger automatic trip matching."""
    from datetime import datetime, timezone
    from .auto_match import process_bouncie_link
    
    logger.info(f"Processing trip_ended event for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    # Extract trip information from payload
    data = payload.get("data", {})
    trip_id = data.get("trip_id") or payload.get("trip_id")
    end_time = data.get("end_time") or data.get("endTime") or payload.get("timestamp")
    
    logger.info(f"Trip ended: trip_id={trip_id}, end_time={end_time}")
    
    # Trigger automatic trip matching for recent trips (last 7 days)
    # This will match the newly ended trip with Turo trips
    try:
        result = await process_bouncie_link(
            db=db,
            account_id=account_id,
            days_back=7,  # Only check recent trips
            skip_existing_matches=False,  # Re-check to catch new matches
            force_rematch=False
        )
        
        if result.get("success"):
            logger.info(f"Automatic trip matching triggered after trip_ended event")
        else:
            logger.warning(f"Trip matching failed after trip_ended: {result.get('error')}")
    except Exception as e:
        logger.exception(f"Error triggering trip matching after trip_ended: {e}")

async def _handle_device_connected(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle device_connected webhook - log device connection."""
    from datetime import datetime, timezone
    
    logger.info(f"Device {imei} connected for account {account_id}, vehicle {vehicle_id}")
    
    # Extract connection information
    data = payload.get("data", {})
    connected_at = data.get("connected_at") or data.get("timestamp") or payload.get("timestamp")
    
    # You could store this in a device status table if needed
    # For now, just log it
    logger.info(f"Device connected at {connected_at}")
    
    # Could update vehicle mapping status or create device status record here

async def _handle_device_disconnected(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle device_disconnected webhook - log device disconnection."""
    from datetime import datetime, timezone
    
    logger.info(f"Device {imei} disconnected for account {account_id}, vehicle {vehicle_id}")
    
    # Extract disconnection information
    data = payload.get("data", {})
    disconnected_at = data.get("disconnected_at") or data.get("timestamp") or payload.get("timestamp")
    
    # You could store this in a device status table if needed
    # For now, just log it
    logger.info(f"Device disconnected at {disconnected_at}")
    
    # Could update vehicle mapping status or create device status record here

async def _handle_vin_change(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle vin_change webhook - update vehicle mapping with new VIN."""
    from datetime import datetime, timezone
    
    logger.info(f"Processing VIN change for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    # Extract new VIN from payload
    data = payload.get("data", {})
    new_vin = (
        data.get("vin") or 
        data.get("new_vin") or
        payload.get("vin") or
        payload.get("new_vin")
    )
    
    if not new_vin:
        logger.warning(f"No VIN found in vin_change payload: {payload}")
        return
    
    # Find the vehicle mapping
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == account_id,
        BouncieVehicleMapping.vehicle_id == vehicle_id,
        BouncieVehicleMapping.imei == imei
    ).first()
    
    if not mapping:
        logger.warning(f"No mapping found for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
        return
    
    # Update VIN
    old_vin = mapping.bouncie_vin
    mapping.bouncie_vin = new_vin
    db.commit()
    db.refresh(mapping)
    
    logger.info(f"Updated VIN for IMEI {imei}: {old_vin} -> {new_vin}")

# ------------------------------ DTC CODE ROUTES ------------------------------

@router.get("/dtc-codes", response_model=APIResponse, tags=["Diagnostics"])
@handle_route_errors("retrieving DTC codes")
async def get_dtc_codes(
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    imei: Optional[str] = Query(None, description="Filter by IMEI"),
    active_only: bool = Query(True, description="Only return active codes"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored DTC codes for authenticated user."""
    query = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == current_user.id
    )
    
    if vehicle_id:
        query = query.filter(BouncieDTCCode.vehicle_id == vehicle_id)
    
    if imei:
        query = query.filter(BouncieDTCCode.imei == imei)
    
    if active_only:
        query = query.filter(BouncieDTCCode.is_active == True)
    
    total = query.count()
    
    codes = query.order_by(BouncieDTCCode.occurred_at.desc()).offset(offset).limit(limit).all()
    
    codes_data = []
    for code in codes:
        vehicle = db.query(Vehicle).filter(Vehicle.id == code.vehicle_id).first() if code.vehicle_id else None
        codes_data.append(
            BouncieDTCCodeOut(
                id=code.id,
                vehicle_id=code.vehicle_id,
                vehicle_name=vehicle.name if vehicle else None,
                imei=code.imei,
                code=code.code,
                description=code.description,
                is_active=code.is_active,
                occurred_at=code.occurred_at,
                cleared_at=code.cleared_at,
                created_at=code.created_at,
                updated_at=code.updated_at,
            ).model_dump()
        )
    
    return APIResponse(
        success=True,
        data={
            "codes": codes_data,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.post("/dtc-codes/{code_id}/clear", response_model=APIResponse, tags=["Diagnostics"])
@handle_route_errors("clearing DTC code", rollback_db=True)
async def clear_dtc_code(
    code_id: int = Path(..., description="DTC code ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a DTC code as cleared."""
    code = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.id == code_id,
        BouncieDTCCode.account_id == current_user.id
    ).first()
    
    if not code:
        raise HTTPException(status_code=404, detail=f"DTC code {code_id} not found")
    
    if not code.is_active:
        return APIResponse(
            success=True,
            data={"message": "Code already cleared", "code": BouncieDTCCodeOut.model_validate(code).model_dump()}
        )
    
    code.is_active = False
    code.cleared_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(code)
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == code.vehicle_id).first() if code.vehicle_id else None
    
    logger.info(f"Cleared DTC code {code.code} for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "message": "DTC code cleared successfully",
            "code": BouncieDTCCodeOut(
                id=code.id,
                vehicle_id=code.vehicle_id,
                vehicle_name=vehicle.name if vehicle else None,
                imei=code.imei,
                code=code.code,
                description=code.description,
                is_active=code.is_active,
                occurred_at=code.occurred_at,
                cleared_at=code.cleared_at,
                created_at=code.created_at,
                updated_at=code.updated_at,
            ).model_dump()
        }
    )

# ------------------------------ END OF FILE ------------------------------
