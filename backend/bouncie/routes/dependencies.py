# ------------------------------ IMPORTS ------------------------------
from fastapi import HTTPException, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..service import BouncieService
from ..helpers import trip_to_dict, normalize_imei
from ..schemas import (
    BouncieTripMatchOut, BouncieTripMatchDetailOut,
    BouncieVehicleMappingOut, BouncieDTCCodeOut, APIResponse
)
from core.database import get_db
from core.database.models import Trip, BouncieTripMatch, Account, Vehicle, BouncieVehicleMapping, BouncieDTCCode
from core.security.auth import get_current_active_user
from datetime import datetime, timedelta, timezone
from ..data_fetcher import fetch_trips_in_date_range

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_bouncie_service(
    db: Session = Depends(get_db),
    current_user: Account = Depends(get_current_active_user)
) -> BouncieService:
    """Dependency to get BouncieService instance for current user."""
    return BouncieService(db=db, account=current_user)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def _ensure_access_token(service: BouncieService) -> None:
    """Ensure service has a valid access token, raising HTTPException if not available."""
    if not service.access_token:
        service._load_tokens()
        if not service.access_token:
            raise HTTPException(
                status_code=401,
                detail="Bouncie not connected. Please connect Bouncie first."
            )

def _get_vehicle_name(db: Session, vehicle_id: Optional[int], account_id: int) -> Optional[str]:
    """Get vehicle name by ID, scoped to account."""
    if vehicle_id is None:
        return None
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.account_id == account_id
    ).first()
    return vehicle.name if vehicle else None

def _build_match_out(match: BouncieTripMatch, trip: Optional[Trip] = None, include_full_data: bool = False) -> BouncieTripMatchOut | BouncieTripMatchDetailOut:
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

def _build_mapping_out(mapping: BouncieVehicleMapping, vehicle_name: Optional[str]) -> dict:
    """Build BouncieVehicleMappingOut dict from mapping."""
    return BouncieVehicleMappingOut(
        id=mapping.id,
        vehicle_id=mapping.vehicle_id,
        vehicle_name=vehicle_name,
        imei=mapping.imei,
        bouncie_nickname=mapping.bouncie_nickname,
        bouncie_vin=mapping.bouncie_vin,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    ).model_dump()

def _build_dtc_code_out(code: BouncieDTCCode, vehicle_name: Optional[str]) -> dict:
    """Build BouncieDTCCodeOut dict from code."""
    return BouncieDTCCodeOut(
        id=code.id,
        vehicle_id=code.vehicle_id,
        vehicle_name=vehicle_name,
        imei=code.imei,
        code=code.code,
        description=code.description,
        is_active=code.is_active,
        occurred_at=code.occurred_at,
        cleared_at=code.cleared_at,
        created_at=code.created_at,
        updated_at=code.updated_at,
    ).model_dump()

def _handle_service_result(result: dict, error_msg: str) -> APIResponse:
    """Handle service result and return APIResponse or raise HTTPException."""
    if result.get("success"):
        return APIResponse(success=True, data=result.get("data", []))
    else:
        raise HTTPException(
            status_code=500,
            detail=f"{error_msg}: {result.get('error')}"
        )

def _check_mapping_exists(
    db: Session,
    account_id: int,
    vehicle_id: Optional[int] = None,
    imei: Optional[str] = None,
    exclude_id: Optional[int] = None
) -> Optional[BouncieVehicleMapping]:
    """Check if a mapping exists for given criteria."""
    query = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == account_id
    )
    if vehicle_id is not None:
        query = query.filter(BouncieVehicleMapping.vehicle_id == vehicle_id)
    if imei is not None:
        query = query.filter(BouncieVehicleMapping.imei == normalize_imei(imei))
    if exclude_id is not None:
        query = query.filter(BouncieVehicleMapping.id != exclude_id)
    return query.first()

async def _fetch_turo_trips(
    db: Session,
    current_user: Account,
    trip_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch Turo trips from database."""
    if trip_id is not None:
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
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    trips = await fetch_trips_in_date_range(
        service=service,
        start_date=start_date,
        end_date=end_date,
        imei=imei
    )
    return trips

# ------------------------------ END OF FILE ------------------------------