# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from typing import Optional
import logging
from datetime import datetime, timedelta, timezone

from ..service import BouncieService
from ..helpers import format_date_for_api, get_odometer_at_time_from_trips
from ..schemas import APIResponse
from core.database import get_db
from core.database.models import BouncieVehicleMapping, Account, VehicleOdometerHistory
from core.security.auth import get_current_active_user
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session
from sqlalchemy import func
from .dependencies import get_bouncie_service, _ensure_access_token

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ LIVE DATA PROXY ROUTES ------------------------------

@router.get("/vehicles", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("fetching vehicles")
async def get_vehicles_proxy(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get all vehicles from Bouncie with their current status."""
    _ensure_access_token(service)
    result = await service.get_vehicles()
    
    if result.get("success"):
        return APIResponse(success=True, data={"vehicles": result.get("data", [])})
    else:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicles: {result.get('error')}")

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
    """Get trips from Bouncie. Note: Bouncie API requires IMEI parameter."""
    _ensure_access_token(service)
    
    if not imei:
        raise HTTPException(status_code=400, detail="IMEI parameter is required by Bouncie API")
    
    normalized_imei = imei.strip().replace("-", "").replace(" ", "")
    
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id,
        BouncieVehicleMapping.imei == normalized_imei
    ).first()
    
    if not mapping:
        raise HTTPException(
            status_code=403,
            detail=f"IMEI {normalized_imei} is not mapped to your account"
        )
    
    result = await service.get_trips(gps_format=gps_format, start_date=start_date, end_date=end_date, imei=normalized_imei)
    
    if result.get("success"):
        return APIResponse(success=True, data={"trips": result.get("data", [])})
    else:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trips: {result.get('error')}")

@router.get("/live", response_model=APIResponse, tags=["Live Data"])
@handle_route_errors("fetching live vehicle data")
async def get_live_vehicles(
    include_trips_today: bool = Query(False, description="Include today's trips (slower, makes N API calls)"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get aggregated live vehicle data with location, speed, fuel, and trip information."""
    _ensure_access_token(service)
    
    vehicles_result = await service.get_vehicles()
    if not vehicles_result.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicles: {vehicles_result.get('error')}")
    
    vehicles = vehicles_result.get("data", [])
    if not vehicles:
        return APIResponse(success=True, data={"vehicles": []})
    
    mappings = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).all()
    imei_to_vehicle_id = {mapping.imei: mapping.vehicle_id for mapping in mappings}
    
    now = datetime.now(timezone.utc)
    today = now.date()
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    today_str = format_date_for_api(today_start)
    now_str = format_date_for_api(now)
    
    live_vehicles = []
    
    for vehicle in vehicles:
        imei = vehicle.get('imei')
        if not imei:
            continue
        
        vehicle_id = imei_to_vehicle_id.get(imei)
        if not vehicle_id:
            continue
        
        stats = vehicle.get('stats')
        location = _extract_location(vehicle, stats)
        
        if not location:
            continue
        
        trips_today = []
        miles_driven_today = 0.0
        active_trip = None
        
        if include_trips_today:
            trips_result = await service.get_trips(gps_format="geojson", start_date=today_str, end_date=now_str, imei=imei)
            trips_today = trips_result.get("data", []) if trips_result.get("success") else []
            miles_driven_today = sum(trip.get('distance', 0) or 0 for trip in trips_today)
            active_trip = next((trip for trip in trips_today if not trip.get('endTime')), None)
        
        if active_trip and active_trip.get('gps'):
            gps = active_trip.get('gps')
            if isinstance(gps, dict) and gps.get('coordinates'):
                coords = gps.get('coordinates')
                if isinstance(coords, list) and len(coords) > 0:
                    last_coord = coords[-1]
                    if isinstance(last_coord, list) and len(last_coord) >= 2:
                        location = {"lat": float(last_coord[1]), "lon": float(last_coord[0])}
        
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
        
        status = "parked"
        if active_trip:
            status = "moving"
        elif isinstance(stats, dict) and stats.get('isRunning'):
            status = "moving"
        elif vehicle.get('status') == "offline":
            status = "offline"
        
        flags = {}
        if active_trip:
            flags = {
                "rapidAcceleration": active_trip.get('rapidAcceleration') or active_trip.get('rapidAccel') or 0,
                "hardBraking": active_trip.get('hardBraking') or active_trip.get('hardBrake') or 0,
            }
        
        engine_light = False
        if isinstance(stats, dict):
            engine_light = stats.get('mil') or stats.get('checkEngine') or False
        
        if not engine_light:
            engine_light = vehicle.get('mil') or vehicle.get('checkEngine') or False
        
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
            "engineInfo": vehicle.get('standardEngine'),
            "odometer": stats.get('odometer') if isinstance(stats, dict) else None,
        }
        
        live_vehicles.append(live_vehicle)
    
    return APIResponse(success=True, data={"vehicles": live_vehicles})

# ------------------------------ ODOMETER ROUTES ------------------------------

def _extract_location(vehicle: dict, stats: dict) -> Optional[dict]:
    """Extract location from vehicle stats or vehicle data."""
    location = None
    
    if isinstance(stats, dict) and stats.get('location'):
        stats_location = stats.get('location')
        if isinstance(stats_location, dict):
            lat = stats_location.get('lat')
            lon = stats_location.get('lon')
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                location = {"lat": float(lat), "lon": float(lon)}
    
    if not location and vehicle.get('location'):
        vehicle_location = vehicle.get('location')
        if isinstance(vehicle_location, dict):
            lat = vehicle_location.get('lat')
            lon = vehicle_location.get('lon')
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                location = {"lat": float(lat), "lon": float(lon)}
    
    return location

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
    """Get odometer reading at a specific timestamp using Bouncie trips."""
    _ensure_access_token(service)
    
    normalized_imei = imei.strip().replace("-", "").replace(" ", "")
    
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id,
        BouncieVehicleMapping.imei == normalized_imei
    ).first()
    
    if not mapping:
        raise HTTPException(
            status_code=403,
            detail=f"IMEI {normalized_imei} is not mapped to your account"
        )
    
    try:
        target_time_str = timestamp.replace('Z', '+00:00')
        target_time = datetime.fromisoformat(target_time_str)
        
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)
        else:
            target_time = target_time.astimezone(timezone.utc)
        
        target_time_naive = target_time.replace(tzinfo=None)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid timestamp format. Use ISO format (e.g., 2025-12-27T01:00:00 or 2025-12-27T01:00:00Z). Error: {str(e)}"
        )
    
    start_date = target_time - timedelta(days=days_buffer)
    end_date = target_time + timedelta(days=days_buffer)
    
    start_date_naive = start_date.replace(tzinfo=None)
    end_date_naive = end_date.replace(tzinfo=None)
    
    trips_result = await service.get_trips(
        start_date=format_date_for_api(start_date_naive),
        end_date=format_date_for_api(end_date_naive),
        imei=normalized_imei
    )
    
    if not trips_result.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to fetch trips from Bouncie: {trips_result.get('error', 'Unknown error')}")
    
    trips = trips_result.get("data", [])
    
    result = get_odometer_at_time_from_trips(trips, target_time_naive, imei=normalized_imei)
    
    if result:
        return APIResponse(success=True, data=result)
    else:
        return APIResponse(
            success=False,
            data={
                "message": f"No odometer data found for IMEI {normalized_imei} at timestamp {timestamp}",
                "timestamp": timestamp,
                "imei": normalized_imei,
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
    """Store daily odometer snapshots for all mapped vehicles."""
    _ensure_access_token(service)
    
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
    
    vehicles_result = await service.get_vehicles()
    if not vehicles_result.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicles from Bouncie: {vehicles_result.get('error')}")
    
    bouncie_vehicles = vehicles_result.get("data", []) or []
    imei_to_vehicle = {v.get("imei"): v for v in bouncie_vehicles if v.get("imei")}
    
    now = datetime.now(timezone.utc)
    today = now.date()
    today_datetime = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    
    snapshots_stored = 0
    snapshots_updated = 0
    errors = []
    
    for mapping in mappings:
        try:
            imei = mapping.imei
            vehicle_id = mapping.vehicle_id
            
            bouncie_vehicle = imei_to_vehicle.get(imei)
            if not bouncie_vehicle:
                errors.append(f"Vehicle with IMEI {imei} not found in Bouncie")
                continue
            
            stats = bouncie_vehicle.get('stats', {})
            odometer_miles = None
            
            if isinstance(stats, dict):
                odometer_miles = stats.get('odometer')
            
            if odometer_miles is None:
                odometer_miles = bouncie_vehicle.get('odometer')
            
            if odometer_miles is None:
                errors.append(f"No odometer data for IMEI {imei}")
                continue
            
            existing = db.query(VehicleOdometerHistory).filter(
                VehicleOdometerHistory.vehicle_id == vehicle_id,
                VehicleOdometerHistory.account_id == current_user.id,
                func.date(VehicleOdometerHistory.date) == today
            ).first()
            
            if existing:
                existing.odometer_miles = float(odometer_miles)
                existing.recorded_at = datetime.now(timezone.utc)
                snapshots_updated += 1
            else:
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

# ------------------------------ END OF FILE ------------------------------