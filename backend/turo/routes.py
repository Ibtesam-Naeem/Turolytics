# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from core.services.scraping_service import ScrapingService
from core.db.operations.turo_operations import get_database_stats
from core.utils.api_helpers import validate_credentials, get_account_id
from core.db.database import get_db_session
from core.db.base import Vehicle, Trip, Payout, Review, TripStatus

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

# ------------------------------ DATA RETRIEVAL ENDPOINTS ------------------------------

@router.get("/vehicles")
async def get_vehicles(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None)):
    """Get all vehicles for an account."""
    try:
        if not account_id and not email:
            raise HTTPException(status_code=400, detail="Either account_id or email is required")
        
        if not account_id and email:
            account_id = get_account_id(email)
        
        with get_db_session() as db:
            vehicles = db.query(Vehicle).filter(Vehicle.account_id == account_id).all()
            
            return {
                "success": True,
                "account_id": account_id,
                "vehicles": [vehicle.to_dict() for vehicle in vehicles],
                "count": len(vehicles)
            }
            
    except Exception as e:
        logger.error(f"Error getting vehicles for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get vehicles: {str(e)}")

@router.get("/trips")
async def get_trips(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), status: Optional[str] = Query(None), limit: int = Query(50)):
    """Get trips for an account, optionally filtered by status."""
    try:
        if not account_id and not email:
            raise HTTPException(status_code=400, detail="Either account_id or email is required")
        
        if not account_id and email:
            account_id = get_account_id(email)
        
        with get_db_session() as db:
            query = db.query(Trip).filter(Trip.account_id == account_id)
            
            if status:
                # Convert string to enum
                try:
                    status_enum = TripStatus(status.upper())
                    query = query.filter(Trip.status == status_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid values: {[s.value for s in TripStatus]}")
            
            trips = query.order_by(Trip.created_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "account_id": account_id,
                "trips": [trip.to_dict() for trip in trips],
                "count": len(trips),
                "filters": {"status": status, "limit": limit}
            }
            
    except Exception as e:
        logger.error(f"Error getting trips for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")

@router.get("/earnings")
async def get_earnings(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), limit: int = Query(50)):
    """Get earnings data for an account."""
    try:
        if not account_id and not email:
            raise HTTPException(status_code=400, detail="Either account_id or email is required")
        
        if not account_id and email:
            account_id = get_account_id(email)
        
        with get_db_session() as db:
            payouts = db.query(Payout).filter(Payout.account_id == account_id).order_by(Payout.created_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "account_id": account_id,
                "earnings": [payout.to_dict() for payout in payouts],
                "count": len(payouts),
                "total_amount": sum(float(payout.amount or 0) for payout in payouts)
            }
            
    except Exception as e:
        logger.error(f"Error getting earnings for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get earnings: {str(e)}")

@router.get("/reviews")
async def get_reviews(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None), limit: int = Query(50)):
    """Get reviews for an account."""
    try:
        if not account_id and not email:
            raise HTTPException(status_code=400, detail="Either account_id or email is required")
        
        if not account_id and email:
            account_id = get_account_id(email)
        
        with get_db_session() as db:
            reviews = db.query(Review).filter(Review.account_id == account_id).order_by(Review.created_at.desc()).limit(limit).all()
            
            return {
                "success": True,
                "account_id": account_id,
                "reviews": [review.to_dict() for review in reviews],
                "count": len(reviews),
                "average_rating": sum(float(review.rating or 0) for review in reviews) / len(reviews) if reviews else 0
            }
            
    except Exception as e:
        logger.error(f"Error getting reviews for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary(account_id: Optional[int] = Query(None), email: Optional[str] = Query(None)):
    """Get business analytics summary for an account."""
    try:
        if not account_id and not email:
            raise HTTPException(status_code=400, detail="Either account_id or email is required")
        
        if not account_id and email:
            account_id = get_account_id(email)
        
        with get_db_session() as db:
            # Get counts
            vehicle_count = db.query(Vehicle).filter(Vehicle.account_id == account_id).count()
            trip_count = db.query(Trip).filter(Trip.account_id == account_id).count()
            completed_trips = db.query(Trip).filter(Trip.account_id == account_id, Trip.status == TripStatus.COMPLETED).count()
            cancelled_trips = db.query(Trip).filter(Trip.account_id == account_id, Trip.status == TripStatus.CANCELLED).count()
            review_count = db.query(Review).filter(Review.account_id == account_id).count()
            
            # Get total earnings
            payouts = db.query(Payout).filter(Payout.account_id == account_id).all()
            total_earnings = sum(float(payout.amount or 0) for payout in payouts)
            
            # Get average rating
            reviews = db.query(Review).filter(Review.account_id == account_id).all()
            avg_rating = sum(float(review.rating or 0) for review in reviews) / len(reviews) if reviews else 0
            
            return {
                "success": True,
                "account_id": account_id,
                "summary": {
                    "vehicles": vehicle_count,
                    "total_trips": trip_count,
                    "completed_trips": completed_trips,
                    "cancelled_trips": cancelled_trips,
                    "completion_rate": (completed_trips / trip_count * 100) if trip_count > 0 else 0,
                    "total_earnings": total_earnings,
                    "reviews": review_count,
                    "average_rating": round(avg_rating, 2)
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting analytics summary for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

# ------------------------------ END OF FILE ------------------------------