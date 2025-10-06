# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from .service import BouncieService, get_bouncie_vehicle_data
from core.utils.api_helpers import validate_credentials, get_account_id
from core.db.database import get_db_session

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def check_result(result: Dict[str, Any], operation: str) -> Dict[str, Any]:
    """Check API result and raise HTTPException if failed."""
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Bouncie {operation} failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Bouncie {operation} failed: {error_msg}")
    return result

# ------------------------------ PYDANTIC MODELS ------------------------------

class TokenExchangeRequest(BaseModel):
    authorization_code: str

class TripRequest(BaseModel):
    gps_format: str = "geojson"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    imei: Optional[str] = None

class DatabaseRequest(BaseModel):
    account_email: str
    imei: Optional[str] = None
    limit: Optional[int] = 100
    days: Optional[int] = 30

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(prefix="/bouncie", tags=["bouncie"])

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.get("/auth/url")
async def get_authorization_url(state: Optional[str] = None):
    """Get OAuth 2.0 authorization URL."""
    service = BouncieService()
    url = service.get_authorization_url(state)
    return {"success": True, "data": {"authorization_url": url}}

@router.post("/auth/token")
async def exchange_code_for_token(request: TokenExchangeRequest):
    """Exchange authorization code for access token."""
    service = BouncieService()
    result = await service.exchange_code_for_token(request.authorization_code)
    return check_result(result, "token exchange")

# ------------------------------ VEHICLE ROUTES ------------------------------

@router.get("/vehicles")
async def get_vehicles():
    """Get all vehicles."""
    service = BouncieService()
    result = await service.get_vehicles()
    return check_result(result, "get vehicles")

@router.get("/vehicles/{imei}")
async def get_vehicle_by_imei(imei: str):
    """Get specific vehicle by IMEI."""
    service = BouncieService()
    result = await service.get_vehicle_by_imei(imei)
    return check_result(result, "get vehicle")

@router.get("/vehicles/{imei}/status")
async def get_vehicle_status(imei: str):
    """Get current vehicle status."""
    service = BouncieService()
    result = await service.get_current_vehicle_status(imei)
    return check_result(result, "get vehicle status")

@router.get("/vehicles/{imei}/analytics")
async def get_vehicle_analytics(imei: str):
    """Get comprehensive vehicle analytics."""
    service = BouncieService()
    result = await service.get_vehicle_analytics(imei)
    return check_result(result, "get vehicle analytics")

# ------------------------------ TRIP ROUTES ------------------------------

@router.post("/trips")
async def get_trips(request: TripRequest):
    """Get trips with specified parameters."""
    service = BouncieService()
    result = await service.get_trips(
        gps_format=request.gps_format,
        start_date=request.start_date,
        end_date=request.end_date,
        imei=request.imei
    )
    return check_result(result, "get trips")

@router.get("/trips/recent")
async def get_recent_trips(days: int = Query(7, ge=1, le=30), imei: Optional[str] = None):
    """Get recent trips for the last N days."""
    service = BouncieService()
    result = await service.get_recent_trips(days, imei)
    return check_result(result, "get recent trips")

# ------------------------------ DATABASE ROUTES ------------------------------

@router.post("/db/vehicles/save")
async def save_vehicles_to_db(request: DatabaseRequest):
    """Save vehicles to database."""
    service = BouncieService()
    result = await service.save_vehicles_to_db(request.account_email)
    return check_result(result, "save vehicles to database")

@router.post("/db/trips/save")
async def save_trips_to_db(request: DatabaseRequest):
    """Save trips to database."""
    service = BouncieService()
    result = await service.save_trips_to_db(
        account_email=request.account_email,
        imei=request.imei
    )
    return check_result(result, "save trips to database")

@router.get("/db/trips")
async def get_trips_from_db(
    account_email: str = Query(..., description="Account email"),
    imei: Optional[str] = Query(None, description="Vehicle IMEI"),
    limit: int = Query(100, ge=1, le=1000, description="Number of trips to retrieve")
):
    """Get trips from database."""
    service = BouncieService()
    result = await service.get_trips_from_db(account_email, imei, limit)
    return check_result(result, "get trips from database")

@router.get("/db/trips/stats")
async def get_trip_stats_from_db(
    account_email: str = Query(..., description="Account email"),
    imei: Optional[str] = Query(None, description="Vehicle IMEI"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get trip statistics from database."""
    service = BouncieService()
    result = await service.get_trip_stats_from_db(account_email, imei, days)
    return check_result(result, "get trip statistics from database")

# ------------------------------ WEBHOOK ROUTES ------------------------------

@router.get("/webhooks/events")
async def get_webhook_events():
    """Get list of available webhook events."""
    service = BouncieService()
    events = service.get_webhook_events()
    return {"success": True, "data": {"events": events}}

@router.post("/webhooks/validate")
async def validate_webhook(payload: Dict[str, Any]):
    """Validate webhook payload."""
    service = BouncieService()
    is_valid = service.validate_webhook_payload(payload)
    return {"success": True, "data": {"valid": is_valid}}

# ------------------------------ CONVENIENCE ROUTES ------------------------------

@router.post("/quick-setup")
async def quick_setup(request: TokenExchangeRequest):
    """Quick setup: authenticate and get all vehicle data."""
    result = await get_bouncie_vehicle_data(request.authorization_code)
    return check_result(result, "quick setup")

# ------------------------------ END OF FILE ------------------------------