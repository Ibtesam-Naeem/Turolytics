# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from core.services.scraping_service import ScrapingService
from core.db.operations.turo_operations import get_database_stats
from core.utils.api_helpers import validate_credentials, get_account_id
from core.db.database import get_db_session
from core.db.base import Vehicle, Trip, Payout, Review

logger = logging.getLogger(__name__)

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

def _format_vehicle_data(vehicle) -> Dict[str, Any]:
    """Format vehicle data for API response."""
    return {
        "id": vehicle.id,
        "turo_vehicle_id": vehicle.turo_vehicle_id,
        "name": vehicle.name,
        "year": vehicle.year,
        "make": vehicle.make,
        "model": vehicle.model,
        "trim": vehicle.trim,
        "license_plate": vehicle.license_plate,
        "status": vehicle.status.value if vehicle.status else None,
        "is_active": vehicle.is_active,
        "rating": vehicle.rating,
        "trip_count": vehicle.trip_count,
        "last_trip_at": vehicle.last_trip_at.isoformat() if vehicle.last_trip_at else None,
        "image_url": vehicle.image_url,
        "image_alt": vehicle.image_alt,
        "last_seen_at": vehicle.last_seen_at.isoformat() if vehicle.last_seen_at else None,
        "scraped_at": vehicle.scraped_at.isoformat() if vehicle.scraped_at else None,
        "created_at": vehicle.created_at.isoformat() if vehicle.created_at else None,
        "updated_at": vehicle.updated_at.isoformat() if vehicle.updated_at else None
    }

def _format_trip_data(trip) -> Dict[str, Any]:
    """Format trip data for API response."""
    return {
        "id": trip.id,
        "turo_trip_id": trip.turo_trip_id,
        "turo_trip_url": trip.turo_trip_url,
        "vehicle_id": trip.vehicle_id,
        "trip_dates": trip.trip_dates,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
        "customer_name": trip.customer_name,
        "customer_id": trip.customer_id,
        "customer_info": trip.customer_info,
        "customer_found": trip.customer_found,
        "status": trip.status.value if trip.status else None,
        "cancellation_info": trip.cancellation_info,
        "cancelled_by": trip.cancelled_by,
        "cancelled_date": trip.cancelled_date.isoformat() if trip.cancelled_date else None,
        "price_total": float(trip.price_total) if trip.price_total else None,
        "earnings": float(trip.earnings) if trip.earnings else None,
        "vehicle_image": trip.vehicle_image,
        "customer_profile_image": trip.customer_profile_image,
        "has_customer_photo": trip.has_customer_photo,
        "scraped_at": trip.scraped_at.isoformat() if trip.scraped_at else None,
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
        "updated_at": trip.updated_at.isoformat() if trip.updated_at else None
    }

def _format_earnings_data(payout) -> Dict[str, Any]:
    """Format earnings data for API response."""
    return {
        "id": payout.id,
        "turo_payout_id": payout.turo_payout_id,
        "payout_at": payout.payout_at.isoformat() if payout.payout_at else None,
        "amount": float(payout.amount) if payout.amount else None,
        "method": payout.method,
        "reference": payout.reference,
        "scraped_at": payout.scraped_at.isoformat() if payout.scraped_at else None,
        "created_at": payout.created_at.isoformat() if payout.created_at else None,
        "updated_at": payout.updated_at.isoformat() if payout.updated_at else None
    }

def _format_review_data(review) -> Dict[str, Any]:
    """Format review data for API response."""
    return {
        "id": review.id,
        "turo_review_id": review.turo_review_id,
        "trip_id": review.trip_id,
        "customer_name": review.customer_name,
        "customer_id": review.customer_id,
        "customer_image_url": review.customer_image_url,
        "customer_image_alt": review.customer_image_alt,
        "rating": review.rating,
        "date": review.date.isoformat() if review.date else None,
        "vehicle_info": review.vehicle_info,
        "review_text": review.review_text,
        "areas_of_improvement": review.areas_of_improvement,
        "host_response": review.host_response,
        "has_host_response": review.has_host_response,
        "scraped_at": review.scraped_at.isoformat() if review.scraped_at else None,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None
    }

def _validate_account_id(account_id: int) -> None:
    """Validate account ID is positive."""
    if account_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid account ID")

# ------------------------------ SCRAPING ENDPOINTS ------------------------------

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_all(request: ScrapeRequest) -> ScrapeResponse:
    """Scrape all data types on demand."""
    try:
        validate_credentials(request.email, request.password)
        account_id = get_account_id(request.email)
        task_id = await scraping_service.scrape_all(account_id, request.email, request.password)
        
        logger.info(f"Started all data scraping for {request.email}: {task_id}")
        return ScrapeResponse(
            task_id=task_id,
            account_id=account_id,
            scraper_type="all"
        )
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error starting all data scraping for {request.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start all data scraping: {str(e)}")

# ------------------------------ DATA ACCESS ENDPOINTS ------------------------------

@router.get("/vehicles")
async def get_vehicles(account_id: int) -> Dict[str, Any]:
    """Get scraped vehicles data for an account."""
    try:
        _validate_account_id(account_id)
        
        with get_db_session() as db:
            vehicles = db.query(Vehicle).filter(Vehicle.account_id == account_id).all()
            vehicles_data = [_format_vehicle_data(vehicle) for vehicle in vehicles]
        
        return {
            "account_id": account_id,
            "vehicles": vehicles_data,
            "count": len(vehicles_data)
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting vehicles for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get vehicles: {str(e)}")

@router.get("/trips")
async def get_trips(account_id: int) -> Dict[str, Any]:
    """Get scraped trips data for an account."""
    try:
        _validate_account_id(account_id)
        
        with get_db_session() as db:
            trips = db.query(Trip).filter(Trip.account_id == account_id).all()
            trips_data = [_format_trip_data(trip) for trip in trips]
        
        return {
            "account_id": account_id,
            "trips": trips_data,
            "count": len(trips_data)
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting trips for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.get("/earnings")
async def get_earnings(account_id: int) -> Dict[str, Any]:
    """Get scraped earnings data for an account."""
    try:
        _validate_account_id(account_id)
        
        with get_db_session() as db:
            payouts = db.query(Payout).filter(Payout.account_id == account_id).all()
            earnings_data = [_format_earnings_data(payout) for payout in payouts]
        
        return {
            "account_id": account_id,
            "earnings": earnings_data,
            "count": len(earnings_data)
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting earnings for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get earnings: {str(e)}")

@router.get("/reviews")
async def get_reviews(account_id: int) -> Dict[str, Any]:
    """Get scraped reviews data for an account."""
    try:
        _validate_account_id(account_id)
        
        with get_db_session() as db:
            reviews = db.query(Review).filter(Review.account_id == account_id).all()
            reviews_data = [_format_review_data(review) for review in reviews]
        
        return {
            "account_id": account_id,
            "reviews": reviews_data,
            "count": len(reviews_data)
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting reviews for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")

# ------------------------------ UTILITY ENDPOINTS ------------------------------

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a scraping task."""
    try:
        task_status = scraping_service.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "data": task_status
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/accounts/{account_id}/stats")
async def get_account_stats(account_id: int) -> Dict[str, Any]:
    """Get statistics for a specific account."""
    try:
        _validate_account_id(account_id)
        
        stats = get_database_stats(account_id)
        stats = {
            "account_id": account_id,
            "database_stats": stats,
            "scraping_tasks": scraping_service.get_task_count()
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting stats for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account stats: {str(e)}")

# ------------------------------ END OF FILE ------------------------------