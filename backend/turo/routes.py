# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Query, Depends, HTTPException, Path
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from core.services.scraping_service import ScrapingService
from core.utils.api_helpers import validate_credentials, get_account_id
from core.utils.serializers import serialize_models, paginate_response
from core.database import get_db
from sqlalchemy.orm import Session
from .service import TuroDataService
from .schemas import (
    APIResponse,
    TripOut,
    VehicleOut,
    ReviewOut,
    EarningsBreakdownOut,
    VehicleEarningsOut,
)

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ SERVICES ------------------------------
scraping_service = ScrapingService()

# ------------------------------ CONSTANTS ------------------------------
SCRAPER_MAP = {
    "all": scraping_service.scrape_all,
    "vehicles": scraping_service.scrape_vehicles,
    "trips": scraping_service.scrape_trips,
    "reviews": scraping_service.scrape_reviews,
    "earnings": scraping_service.scrape_earnings,
}

# ------------------------------ PYDANTIC MODELS ------------------------------

class ScrapeRequest(BaseModel):
    email: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "your_password"
            }
        }

class ScrapeResponse(BaseModel):
    task_id: str
    account_id: int
    scraper_type: str

# ------------------------------ SCRAPING ENDPOINTS ------------------------------

@router.get("/scrape/{task_id}/status", response_model=APIResponse, tags=["Scraping"])
async def get_scrape_status(task_id: str = Path(..., description="Task ID from scrape endpoint")):
    """Get the status of a scraping task."""
    status = scraping_service.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return APIResponse(
        success=True,
        data=status
    )

@router.post("/scrape/{scraper_type}", response_model=ScrapeResponse, tags=["Scraping"])
async def scrape_data(
    request: ScrapeRequest,
    scraper_type: str = Path(..., pattern="^(all|vehicles|trips|reviews|earnings)$", description="Type of data to scrape")
) -> ScrapeResponse:
    """Scrape data of specified type on demand."""
    validate_credentials(request.email, request.password)
    account_id = get_account_id(request.email)
    
    try:
        task_id = await SCRAPER_MAP[scraper_type](account_id, request.email, request.password)
        logger.info(f"Started {scraper_type} scraping for {request.email}: {task_id}")
        return ScrapeResponse(task_id=task_id, account_id=account_id, scraper_type=scraper_type)
    except Exception as e:
        logger.error(f"Failed to start {scraper_type} scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")

# ------------------------------ DEPENDENCY INJECTION ------------------------------

def get_turo_data_service(db: Session = Depends(get_db)) -> TuroDataService:
    """Dependency to get TuroDataService instance."""
    return TuroDataService(db)

# ------------------------------ DATA ENDPOINTS ------------------------------

@router.get("/data/trips", response_model=APIResponse, response_model_exclude_none=True, tags=["Trips"])
async def get_trips(
    account_id: int = Query(..., description="Turo account ID"),
    trip_id: Optional[str] = Query(None, description="Filter by specific trip ID"),
    status: Optional[str] = Query(None, description="Filter by trip status (COMPLETED, CANCELLED, etc.)"),
    trip_type: Optional[str] = Query(None, description="Filter by trip type (booked_trips, trip_history)"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Filter trips created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter trips created on or before this date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get trips with filtering and pagination."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, 
            detail="start_date must be before or equal to end_date"
        )
    
    trips, total = service.get_trips(
        account_id=account_id,
        trip_id=trip_id,
        status=status,
        trip_type=trip_type,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return APIResponse(
        success=True,
        data=paginate_response(trips, total, TripOut, limit, offset, items_key="trips")
    )

@router.get("/data/vehicles", response_model=APIResponse, response_model_exclude_none=True, tags=["Vehicles"])
async def get_vehicles(
    account_id: int = Query(..., description="Turo account ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    license_plate: Optional[str] = Query(None, description="Filter by license plate"),
    status: Optional[str] = Query(None, description="Filter by status (Listed, Snoozed)"),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get vehicles with filtering."""
    vehicles, total = service.get_vehicles(
        account_id=account_id,
        vehicle_id=vehicle_id,
        license_plate=license_plate,
        status=status
    )
    
    return APIResponse(
        success=True,
        data={
            "vehicles": serialize_models(vehicles, VehicleOut),
            "total": total
        }
    )

@router.get("/data/reviews", response_model=APIResponse, response_model_exclude_none=True, tags=["Reviews"])
async def get_reviews(
    account_id: int = Query(..., description="Turo account ID"),
    review_id: Optional[int] = Query(None, description="Filter by review ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum rating"),
    has_response: Optional[bool] = Query(None, description="Filter by host response"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get reviews with filtering and pagination."""
    reviews, total = service.get_reviews(
        account_id=account_id,
        review_id=review_id,
        vehicle_id=vehicle_id,
        min_rating=min_rating,
        has_response=has_response,
        limit=limit,
        offset=offset
    )
    
    return APIResponse(
        success=True,
        data=paginate_response(reviews, total, ReviewOut, limit, offset, items_key="reviews")
    )

@router.get("/data/earnings", response_model=APIResponse, response_model_exclude_none=True, tags=["Earnings"])
async def get_earnings(
    account_id: int = Query(..., description="Turo account ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get earnings data."""
    breakdowns, vehicle_earnings = service.get_earnings(account_id=account_id, year=year)
    
    return APIResponse(
        success=True,
        data={
            "breakdown": serialize_models(breakdowns, EarningsBreakdownOut),
            "vehicle_earnings": serialize_models(vehicle_earnings, VehicleEarningsOut),
            "total_breakdown_items": len(breakdowns),
            "total_vehicles": len(vehicle_earnings)
        }
    )

# ------------------------------ END OF FILE ------------------------------
