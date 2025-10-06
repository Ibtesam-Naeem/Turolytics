# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from core.services.scraping_service import ScrapingService
from core.db.operations.turo_operations import get_database_stats
from core.utils.api_helpers import validate_credentials, get_account_id
from core.db.database import get_db_session
from core.db.base import Vehicle, Trip, Payout, Review, TripStatus

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

def get_account_id_from_params(account_id: Optional[int], email: Optional[str]) -> int:
    """Get account ID from either account_id or email parameter."""
    if not account_id and not email:
        raise HTTPException(status_code=400, detail="Either account_id or email is required")
    
    if not account_id and email:
        return get_account_id(email)
    
    return account_id

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

@router.get("/accounts/{account_id}/stats")
async def get_account_stats(account_id: int) -> Dict[str, Any]:
    """Get statistics for a specific account."""
    try:
        if account_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid account ID")
        
        stats = {
            "account_id": account_id,
            "database_stats": get_database_stats(account_id),
            "scraping_tasks": scraping_service.get_task_count()
        }
        return create_success_response(stats)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting stats for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account stats: {str(e)}")

# ------------------------------ DATA RETRIEVAL ENDPOINTS ------------------------------

@router.get("/vehicles")
async def get_vehicles(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None)):
    """Get all vehicles for an account."""
    try:
        account_id = get_account_id_from_params(account_id, email)
        
        with get_db_session() as db:
            vehicles = db.query(Vehicle).filter(Vehicle.account_id == account_id).all()
            return create_success_response(
                [vehicle.to_dict() for vehicle in vehicles],
                count=len(vehicles),
                account_id=account_id
            )
    except Exception as e:
        logger.error(f"Error getting vehicles for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get vehicles: {str(e)}")

@router.get("/trips")
async def get_trips(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), status: Optional[str] = Query(None), limit: int = Query(50)):
    """Get trips for an account, optionally filtered by status."""
    try:
        account_id = get_account_id_from_params(account_id, email)
        
        with get_db_session() as db:
            query = db.query(Trip).filter(Trip.account_id == account_id)
            
            if status:
                try:
                    status_enum = TripStatus(status.upper())
                    query = query.filter(Trip.status == status_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid values: {[s.value for s in TripStatus]}")
            
            trips = query.order_by(Trip.created_at.desc()).limit(limit).all()
            
            return create_success_response(
                [trip.to_dict() for trip in trips],
                count=len(trips),
                account_id=account_id,
                filters={"status": status, "limit": limit}
            )
    except Exception as e:
        logger.error(f"Error getting trips for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.get("/earnings")
async def get_earnings(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), limit: int = Query(50)):
    """Get earnings data for an account."""
    try:
        account_id = get_account_id_from_params(account_id, email)
        
        with get_db_session() as db:
            payouts = db.query(Payout).filter(Payout.account_id == account_id).order_by(Payout.created_at.desc()).limit(limit).all()
            total_amount = sum(safe_float(payout.amount) or 0 for payout in payouts)
            
            return create_success_response(
                [payout.to_dict() for payout in payouts],
                count=len(payouts),
                account_id=account_id,
                total_amount=total_amount
            )
    except Exception as e:
        logger.error(f"Error getting earnings for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get earnings: {str(e)}")

@router.get("/reviews")
async def get_reviews(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), limit: int = Query(50)):
    """Get reviews for an account."""
    try:
        account_id = get_account_id_from_params(account_id, email)
        
        with get_db_session() as db:
            reviews = db.query(Review).filter(Review.account_id == account_id).order_by(Review.created_at.desc()).limit(limit).all()
            avg_rating = sum(safe_float(review.rating) or 0 for review in reviews) / len(reviews) if reviews else 0
            
            return create_success_response(
                [review.to_dict() for review in reviews],
                count=len(reviews),
                account_id=account_id,
                average_rating=avg_rating
            )
    except Exception as e:
        logger.error(f"Error getting reviews for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None)):
    """Get business analytics summary for an account."""
    try:
        account_id = get_account_id_from_params(account_id, email)
        
        with get_db_session() as db:
            vehicle_count = db.query(Vehicle).filter(Vehicle.account_id == account_id).count()
            trip_count = db.query(Trip).filter(Trip.account_id == account_id).count()
            completed_trips = db.query(Trip).filter(Trip.account_id == account_id, Trip.status == TripStatus.COMPLETED).count()
            cancelled_trips = db.query(Trip).filter(Trip.account_id == account_id, Trip.status == TripStatus.CANCELLED).count()
            review_count = db.query(Review).filter(Review.account_id == account_id).count()
            
            payouts = db.query(Payout).filter(Payout.account_id == account_id).all()
            total_earnings = sum(safe_float(payout.amount) or 0 for payout in payouts)
            
            reviews = db.query(Review).filter(Review.account_id == account_id).all()
            avg_rating = sum(safe_float(review.rating) or 0 for review in reviews) / len(reviews) if reviews else 0
            
            summary = {
                "vehicles": vehicle_count, "total_trips": trip_count, "completed_trips": completed_trips,
                "cancelled_trips": cancelled_trips, "completion_rate": (completed_trips / trip_count * 100) if trip_count > 0 else 0,
                "total_earnings": total_earnings, "reviews": review_count, "average_rating": round(avg_rating, 2)
            }
            
            return create_success_response(summary, account_id=account_id)
    
    except Exception as e:
        logger.error(f"Error getting analytics summary for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

# ------------------------------ END OF FILE ------------------------------