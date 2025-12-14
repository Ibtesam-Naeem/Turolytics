# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta, timezone

from .service import BouncieService
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_trip, match_all_trips
from .utils import trip_to_dict
from .schemas import (
    APIResponse,
    MatchRequest,
    VehicleMappingRequest,
    VehicleMappingUpdateRequest,
    BouncieTripMatchOut,
    BouncieTripMatchDetailOut,
    BouncieVehicleMappingOut,
)
from core.database import get_db
from core.database.models import Trip, BouncieTripMatch, BouncieVehicleMapping, BouncieIntegration, Account, Vehicle
from core.security.auth import get_current_active_user
from sqlalchemy.orm import Session

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
    account: Account,
    trip_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch Turo trips from database."""
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
    service: BouncieService = Depends(get_bouncie_service)
):
    """
    Get Bouncie OAuth authorization URL.
    The user_id is included in the state parameter so the callback knows which account to save tokens for.
    """
    state = str(service.account.user_id)
    url = service.get_authorization_url(state)
    return APIResponse(success=True, data={"authorization_url": url})

@router.get("/auth/status", response_model=APIResponse, tags=["Authentication"])
async def get_integration_status(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if account has an active Bouncie integration.
    Returns integration status and basic info for authenticated user.
    """
    try:
        account = current_user
        
        from core.database.models import BouncieIntegration
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error checking integration status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/auth/disconnect", response_model=APIResponse, tags=["Authentication"])
async def disconnect_integration(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Bouncie integration for authenticated user.
    Removes OAuth tokens and integration data from the database.
    """
    try:
        account = current_user
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=404,
                detail="No Bouncie integration found for this account"
            )
    
        db.delete(integration)
        db.commit()
        
        logger.info(f"Disconnected Bouncie integration for account {account.id}")
        
        return APIResponse(
            success=True,
            data={
                "message": "Bouncie integration disconnected successfully",
                "account_id": account.id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error disconnecting integration: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/auth/delete-all-data", response_model=APIResponse, tags=["Authentication"])
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
    - Integration/OAuth tokens (BouncieIntegration)
    """
    try:
        account = current_user
        
        deletion_summary = {
            "trip_matches_deleted": 0,
            "vehicle_mappings_deleted": 0,
            "integration_deleted": False
        }
        
        trip_matches = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.account_id == account.id
        ).all()
        deletion_summary["trip_matches_deleted"] = len(trip_matches)
        for match in trip_matches:
            db.delete(match)
        
        vehicle_mappings = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
        ).all()
        deletion_summary["vehicle_mappings_deleted"] = len(vehicle_mappings)
        for mapping in vehicle_mappings:
            db.delete(mapping)
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        if integration:
            db.delete(integration)
            deletion_summary["integration_deleted"] = True
        
        db.commit()
        
        logger.info(
            f"Deleted all Bouncie data for account {account.id}: "
            f"{deletion_summary['trip_matches_deleted']} trip matches, "
            f"{deletion_summary['vehicle_mappings_deleted']} vehicle mappings, "
            f"integration: {deletion_summary['integration_deleted']}"
        )
        
        return APIResponse(
            success=True,
            data={
                "message": "All Bouncie data deleted successfully",
                "account_id": account.id,
                "deletion_summary": deletion_summary
            }
        )
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error deleting all Bouncie data: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/auth/token", response_model=APIResponse, tags=["Authentication"])
async def get_access_token(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get access token for frontend to use directly with Bouncie API.
    Returns temporary access token that frontend can use to call Bouncie API directly.
    """
    try:
        account = current_user
        
        integration = db.query(BouncieIntegration).filter(
            BouncieIntegration.account_id == account.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=404,
                detail="Bouncie not connected for this account"
            )
        
        service = BouncieService(db=db, account=account)
        
        if integration.expires_at and integration.expires_at < datetime.now(timezone.utc):
            logger.info(f"Token expired for account {account.id}, refreshing...")
            refresh_success = await service._refresh_access_token()
            if not refresh_success:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired and refresh failed. Please reconnect Bouncie."
                )
        
        service._load_tokens()
        
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="No access token available. Please reconnect Bouncie."
            )
        
        expires_in = 3600
        if integration.expires_at:
            expires_in = int((integration.expires_at - datetime.now(timezone.utc)).total_seconds())
            expires_in = max(0, expires_in)
        
        return APIResponse(
            success=True,
            data={
                "access_token": service.access_token,
                "expires_in": expires_in,
                "token_type": "Bearer"
            }
        )
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error getting access token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ STORED MATCH DATA ROUTES ------------------------------

@router.get("/matches", response_model=APIResponse, tags=["Stored Data"])
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
    try:
        account = current_user
        
        query = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.account_id == account.id
        )
        
        if trip_id:
            trip = db.query(Trip).filter(
                Trip.account_id == account.id,
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
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error retrieving stored matches: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/matches/{match_id}", response_model=APIResponse, tags=["Stored Data"])
async def get_stored_match_detail(
    match_id: int = Path(..., description="Match ID"),
    include_full_data: bool = Query(False, description="Include full coordinates and match_data"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific stored match."""
    try:
        account = current_user
        
        match = db.query(BouncieTripMatch).filter(
            BouncieTripMatch.id == match_id,
            BouncieTripMatch.account_id == account.id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        
        trip = db.query(Trip).filter(Trip.id == match.trip_id).first()
        match_out = _build_match_out(match, trip, include_full_data=include_full_data)
        
        return APIResponse(success=True, data=match_out.model_dump())
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error retrieving match detail: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ VEHICLE MAPPING ROUTES ------------------------------

@router.get("/mappings", response_model=APIResponse, tags=["Stored Data"])
async def get_vehicle_mappings(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get stored vehicle mappings (Turo vehicles linked to Bouncie IMEIs)."""
    try:
        account = current_user
        
        query = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.account_id == account.id
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving vehicle mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
async def get_vehicle_mapping_detail(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific vehicle mapping by ID."""
    try:
        account = current_user
        
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

@router.post("/mappings", response_model=APIResponse, tags=["Stored Data"])
async def create_vehicle_mapping(
    request: VehicleMappingRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle mapping (link Turo vehicle to Bouncie IMEI).
    """
    try:
        account = current_user
        
        vehicle = db.query(Vehicle).filter(
            Vehicle.id == request.vehicle_id,
            Vehicle.account_id == account.id
        ).first()
        
        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail=f"Vehicle {request.vehicle_id} not found for this account"
            )
        
        existing_mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.vehicle_id == request.vehicle_id,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if existing_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Vehicle {request.vehicle_id} already has a Bouncie mapping (ID: {existing_mapping.id})"
            )
        
        existing_imei = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.imei == request.imei,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if existing_imei:
            raise HTTPException(
                status_code=400,
                detail=f"IMEI {request.imei} is already mapped to vehicle {existing_imei.vehicle_id}"
            )
        
        mapping = BouncieVehicleMapping(
            account_id=account.id,
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating vehicle mapping: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
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
    try:
        account = current_user
        
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.id == mapping_id,
            BouncieVehicleMapping.account_id == account.id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
        
        if request.vehicle_id is not None and request.vehicle_id != mapping.vehicle_id:
            vehicle = db.query(Vehicle).filter(
                Vehicle.id == request.vehicle_id,
                Vehicle.account_id == account.id
            ).first()
            
            if not vehicle:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vehicle {request.vehicle_id} not found for this account"
                )
            
            existing_mapping = db.query(BouncieVehicleMapping).filter(
                BouncieVehicleMapping.vehicle_id == request.vehicle_id,
                BouncieVehicleMapping.account_id == account.id,
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
                BouncieVehicleMapping.account_id == account.id,
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
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error updating vehicle mapping: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/mappings/{mapping_id}", response_model=APIResponse, tags=["Stored Data"])
async def delete_vehicle_mapping(
    mapping_id: int = Path(..., description="Mapping ID"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a vehicle mapping.
    This will unlink the Turo vehicle from the Bouncie IMEI.
    """
    try:
        account = current_user
        
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.id == mapping_id,
            BouncieVehicleMapping.account_id == account.id
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
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error deleting vehicle mapping: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ ACTION ROUTES ------------------------------

@router.post("/matches/match", response_model=APIResponse, tags=["Actions"])
async def match_trips(
    request: MatchRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Real-time trip matching: Match Turo trips with Bouncie trips."""
    try:
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
    
    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Error matching trips: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/matches/sync", response_model=APIResponse, tags=["Actions"])
async def sync_matches(
    days_back: int = Query(365, ge=1, le=365, description="Number of days back to fetch"),
    skip_existing: bool = Query(True, description="Skip trips that already have matches"),
    force_rematch: bool = Query(False, description="Force re-matching of all trips (overrides skip_existing)"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Re-trigger automatic matching process. Fetches recent trips and matches them with Turo trips, storing results in database. By default, skips trips that already have matches for faster processing. Set force_rematch=True to re-match all trips."""
    try:
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

# ------------------------------ END OF FILE ------------------------------
