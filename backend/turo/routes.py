# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from core.services.scraping_service import ScrapingService
from core.utils.api_helpers import validate_credentials, get_account_id

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None

def safe_iso_format(dt) -> Optional[str]:
    """Safely format datetime to ISO string."""
    return dt.isoformat() if dt else None

def create_success_response(data: Any, count: Optional[int] = None, **kwargs) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {"success": True, "data": data}
    if count is not None:
        response["count"] = count
    response.update(kwargs)
    return response

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(prefix="/turo", tags=["turo"])

# ------------------------------ SERVICES ------------------------------
scraping_service = ScrapingService()

# ------------------------------ PYDANTIC MODELS ------------------------------

class ScrapeRequest(BaseModel):
    email: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "your_password"
            }
        }

class ScrapeResponse(BaseModel):
    task_id: str
    account_id: int
    scraper_type: str

class DataResponse(BaseModel):
    account_id: int
    count: int

# ------------------------------ HELPER FUNCTIONS ------------------------------

def format_vehicle_data(vehicle) -> Dict[str, Any]:
    """Format vehicle data for API response."""
    return {
        "id": vehicle.id, "turo_vehicle_id": vehicle.turo_vehicle_id, "name": vehicle.name,
        "year": vehicle.year, "make": vehicle.make, "model": vehicle.model, "trim": vehicle.trim,
        "license_plate": vehicle.license_plate, "status": vehicle.status.value if vehicle.status else None,
        "is_active": vehicle.is_active, "rating": vehicle.rating, "trip_count": vehicle.trip_count,
        "last_trip_at": safe_iso_format(vehicle.last_trip_at), "image_url": vehicle.image_url,
        "image_alt": vehicle.image_alt, "last_seen_at": safe_iso_format(vehicle.last_seen_at),
        "scraped_at": safe_iso_format(vehicle.scraped_at), "created_at": safe_iso_format(vehicle.created_at),
        "updated_at": safe_iso_format(vehicle.updated_at)
    }

def format_trip_data(trip) -> Dict[str, Any]:
    """Format trip data for API response."""
    return {
        "id": trip.id, "turo_trip_id": trip.turo_trip_id, "turo_trip_url": trip.turo_trip_url,
        "vehicle_id": trip.vehicle_id, "trip_dates": trip.trip_dates,
        "start_date": safe_iso_format(trip.start_date), "end_date": safe_iso_format(trip.end_date),
        "customer_name": trip.customer_name, "customer_id": trip.customer_id,
        "customer_info": trip.customer_info, "customer_found": trip.customer_found,
        "status": trip.status.value if trip.status else None, "cancellation_info": trip.cancellation_info,
        "cancelled_by": trip.cancelled_by, "cancelled_date": safe_iso_format(trip.cancelled_date),
        "price_total": safe_float(trip.price_total), "earnings": safe_float(trip.earnings),
        "vehicle_image": trip.vehicle_image, "customer_profile_image": trip.customer_profile_image,
        "has_customer_photo": trip.has_customer_photo, "scraped_at": safe_iso_format(trip.scraped_at),
        "created_at": safe_iso_format(trip.created_at), "updated_at": safe_iso_format(trip.updated_at)
    }

def format_earnings_data(payout) -> Dict[str, Any]:
    """Format earnings data for API response."""
    return {
        "id": payout.id, "turo_payout_id": payout.turo_payout_id,
        "payout_at": safe_iso_format(payout.payout_at), "amount": safe_float(payout.amount),
        "method": payout.method, "reference": payout.reference,
        "scraped_at": safe_iso_format(payout.scraped_at), "created_at": safe_iso_format(payout.created_at),
        "updated_at": safe_iso_format(payout.updated_at)
    }

def format_review_data(review) -> Dict[str, Any]:
    """Format review data for API response."""
    return {
        "id": review.id, "turo_review_id": review.turo_review_id, "trip_id": review.trip_id,
        "customer_name": review.customer_name, "customer_id": review.customer_id,
        "customer_image_url": review.customer_image_url, "customer_image_alt": review.customer_image_alt,
        "rating": review.rating, "date": safe_iso_format(review.date), "vehicle_info": review.vehicle_info,
        "review_text": review.review_text, "areas_of_improvement": review.areas_of_improvement,
        "host_response": review.host_response, "has_host_response": review.has_host_response,
        "scraped_at": safe_iso_format(review.scraped_at), "created_at": safe_iso_format(review.created_at),
        "updated_at": safe_iso_format(review.updated_at)
    }

# ------------------------------ SCRAPING ENDPOINTS ------------------------------

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_all(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape all data types on demand."""
    try:
        validate_credentials(request.email, request.password)
        account_id = get_account_id(request.email)
        task_id = await scraping_service.scrape_all(account_id, request.email, request.password)
        
        logger.info(f"Started all data scraping for {request.email}: {task_id}")
        return ScrapeResponse(task_id=task_id, account_id=account_id, scraper_type="all")
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error starting all data scraping for {request.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start all data scraping: {str(e)}")

# ------------------------------ UTILITY ENDPOINTS ------------------------------

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a scraping task."""
    try:
        task_status = scraping_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        return create_success_response(task_status)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


# ------------------------------ END OF FILE ------------------------------