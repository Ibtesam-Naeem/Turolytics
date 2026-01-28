# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional
import logging

from ..service import BouncieService
from ..matching import match_trip, match_all_trips
from ..trip_processor import process_bouncie_link
from ..schemas import APIResponse, MatchRequest
from ..constants import DEFAULT_SYNC_DAYS_BACK
from core.database import get_db
from core.database.models import Trip, BouncieTripMatch, Account
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session
from .dependencies import get_bouncie_service, _build_match_out, _fetch_turo_trips, _fetch_bouncie_trips, _ensure_access_token

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

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
    """Get stored Bouncie trip matches from the database."""
    query = db.query(BouncieTripMatch).filter(
        BouncieTripMatch.account_id == current_user.id
    )
    
    if trip_id is not None:
        trip = db.query(Trip).filter(
            Trip.account_id == current_user.id,
            Trip.trip_id == trip_id
        ).first()
        if not trip:
            return APIResponse(success=True, data={"matches": [], "total": 0, "limit": limit, "offset": offset})
        query = query.filter(BouncieTripMatch.trip_id == trip.id)
    
    query = query.order_by(BouncieTripMatch.id.desc())
    
    total = query.count()
    
    matches = query.offset(offset).limit(limit).all()
    
    if not matches:
        return APIResponse(success=True, data={"matches": [], "total": total, "limit": limit, "offset": offset})
    
    trip_ids = [match.trip_id for match in matches if match.trip_id is not None]
    trips_dict = {trip.id: trip for trip in db.query(Trip).filter(
        Trip.id.in_(trip_ids),
        Trip.account_id == current_user.id
    ).all()}
    
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
    
    trip = db.query(Trip).filter(
        Trip.id == match.trip_id,
        Trip.account_id == current_user.id
    ).first()
    match_out = _build_match_out(match, trip, include_full_data=include_full_data)
    
    return APIResponse(success=True, data={"match": match_out.model_dump()})

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
    else:
        _ensure_access_token(service)
    
    all_bouncie_trips = await _fetch_bouncie_trips(service, request.days_back, request.imei)
    if not all_bouncie_trips:
        return APIResponse(success=True, data={"matches": [], "message": "No Bouncie trips found"})
    
    if request.trip_id is not None:
        turo_trip = turo_trips[0]
        match_result = match_trip(
            turo_trip,
            all_bouncie_trips,
            vehicle_imei=request.imei
        )
        
        return APIResponse(
            success=True,
            data={
                "matches": [{
                    "turo_trip": turo_trip,
                    "matched_bouncie_trip": match_result
                }]
            }
        )
    else:
        matches = match_all_trips(turo_trips, all_bouncie_trips)
        return APIResponse(success=True, data={"matches": matches})

@router.post("/matches/sync", response_model=APIResponse, tags=["Actions"])
@handle_route_errors("syncing matches")
async def sync_matches(
    days_back: int = Query(DEFAULT_SYNC_DAYS_BACK, ge=1, le=365, description="Number of days back to fetch"),
    skip_existing: bool = Query(True, description="Skip trips that already have matches"),
    force_rematch: bool = Query(False, description="Force re-matching of all trips (overrides skip_existing)"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Re-trigger automatic matching process. By default, skips trips that already have matches."""
    result = await process_bouncie_link(
        db=db,
        account_id=current_user.id,
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

# ------------------------------ END OF FILE ------------------------------