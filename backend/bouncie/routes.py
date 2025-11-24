# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

from .service import BouncieService, get_bouncie_vehicle_data
from .data_fetcher import fetch_trips_in_date_range
from .matching import match_trip, match_all_trips
from core.database import get_db
from core.database.models import Trip
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

def check_result(result: Dict[str, Any], operation: str) -> Dict[str, Any]:
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Bouncie {operation} failed: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Bouncie {operation} failed: {error_msg}")
    return result

# ------------------------------ PYDANTIC MODELS ------------------------------

class TokenExchangeRequest(BaseModel):
    authorization_code: str
    account_id: Optional[int] = None

class TripRequest(BaseModel):
    gps_format: str = "geojson"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    imei: Optional[str] = None

class MatchRequest(BaseModel):
    account_id: int
    authorization_code: Optional[str] = None
    trip_id: Optional[str] = None
    imei: Optional[str] = None
    days_back: int = 30

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.get("/auth/url")
async def get_authorization_url(
    state: Optional[str] = None,
    service: BouncieService = Depends(get_bouncie_service)
):
    url = service.get_authorization_url(state)
    return {"success": True, "data": {"authorization_url": url}}

@router.post("/auth/token")
async def exchange_code_for_token(
    request: TokenExchangeRequest,
    service: BouncieService = Depends(get_bouncie_service)
):
    if request.account_id:
        service.account_id = request.account_id
        
    result = await service.exchange_code_for_token(request.authorization_code)
    return check_result(result, "token exchange")

# ------------------------------ VEHICLE ROUTES ------------------------------

@router.get("/vehicles")
async def get_vehicles(service: BouncieService = Depends(get_bouncie_service)):
    result = await service.get_vehicles()
    return check_result(result, "get vehicles")

@router.get("/vehicles/{imei}")
async def get_vehicle_by_imei(
    imei: str,
    service: BouncieService = Depends(get_bouncie_service)
):
    result = await service.get_vehicle_by_imei(imei)
    return check_result(result, "get vehicle")

@router.get("/vehicles/{imei}/status")
async def get_vehicle_status(
    imei: str,
    service: BouncieService = Depends(get_bouncie_service)
):
    result = await service.get_current_vehicle_status(imei)
    return check_result(result, "get vehicle status")

@router.get("/vehicles/{imei}/analytics")
async def get_vehicle_analytics(
    imei: str,
    service: BouncieService = Depends(get_bouncie_service)
):
    result = await service.get_vehicle_analytics(imei)
    return check_result(result, "get vehicle analytics")

# ------------------------------ TRIP ROUTES ------------------------------

@router.post("/trips")
async def get_trips(
    request: TripRequest,
    service: BouncieService = Depends(get_bouncie_service)
):
    result = await service.get_trips(
        gps_format=request.gps_format,
        start_date=request.start_date,
        end_date=request.end_date,
        imei=request.imei
    )
    return check_result(result, "get trips")

@router.get("/trips/recent")
async def get_recent_trips(
    days: int = Query(7, ge=1, le=30),
    imei: Optional[str] = None,
    service: BouncieService = Depends(get_bouncie_service)
):
    result = await service.get_recent_trips(days, imei)
    return check_result(result, "get recent trips")

# ------------------------------ WEBHOOK ROUTES ------------------------------

@router.get("/webhooks/events")
async def get_webhook_events(service: BouncieService = Depends(get_bouncie_service)):
    events = service.get_webhook_events()
    return {"success": True, "data": {"events": events}}

@router.post("/webhooks/validate")
async def validate_webhook(
    payload: Dict[str, Any],
    service: BouncieService = Depends(get_bouncie_service)
):
    is_valid = service.validate_webhook_payload(payload)
    return {"success": True, "data": {"valid": is_valid}}

# ------------------------------ CONVENIENCE ROUTES ------------------------------

@router.post("/quick-setup")
async def quick_setup(
    request: TokenExchangeRequest,
    db: Session = Depends(get_db)
):
    result = await get_bouncie_vehicle_data(
        request.authorization_code, 
        db=db, 
        account_id=request.account_id
    )
    return check_result(result, "quick setup")

# ------------------------------ MATCHING ROUTES ------------------------------

def _trip_to_dict(trip: Trip) -> Dict[str, Any]:
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
    from core.database.models import Account
    
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
        return [_trip_to_dict(trip)]
    
    trips = db.query(Trip).filter(
        Trip.account_id == account.id,
        Trip.status == "COMPLETED"
    ).all()
    return [_trip_to_dict(t) for t in trips]

async def _fetch_bouncie_trips(
    service: BouncieService,
    days_back: int,
    imei: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch Bouncie trips within the specified window while respecting API limits.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    trips = await fetch_trips_in_date_range(
        service=service,
        start_date=start_date,
        end_date=end_date,
        imei=imei
        )
        
    return trips

@router.post("/match/trip")
async def match_trips(
    request: MatchRequest,
    db: Session = Depends(get_db),
    service: BouncieService = Depends(get_bouncie_service)
):
    try:
        if service.account_id != request.account_id:
            service.account_id = request.account_id
            service._load_tokens()
        elif not service.access_token:
            service._load_tokens()
            
        turo_trips = await _fetch_turo_trips(db, request.account_id, request.trip_id)
        if not turo_trips:
            return {"success": True, "data": {"matches": [], "message": "No trips found"}}
        
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
            return {"success": True, "data": {"matches": [], "message": "No Bouncie trips found"}}
        
        if request.trip_id:
            turo_trip = turo_trips[0]
            match_result = match_trip(
                turo_trip,
                all_bouncie_trips,
                vehicle_imei=request.imei
            )
            
            return {
                "success": True,
                "data": {
                    "turo_trip": turo_trip,
                    "matched_bouncie_trip": match_result
                }
            }
        else:
            matches = match_all_trips(turo_trips, all_bouncie_trips)
            return {"success": True, "data": {"matches": matches}}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error matching trips: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ------------------------------ END OF FILE ------------------------------
