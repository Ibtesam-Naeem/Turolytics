# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

# Import from core
from core.db import (
    get_vehicles_by_account, 
    get_trips_by_account, 
    get_reviews_by_account,
    get_database_stats
)
from core.config.settings import settings
from turo.service import ScrapingService

# ------------------------------ LOGGING ------------------------------
logger = logging.getLogger(__name__)

# ------------------------------ ROUTER ------------------------------
router = APIRouter(prefix="/turo", tags=["Turo"])

# ------------------------------ DEPENDENCIES ------------------------------
def get_scraping_service() -> ScrapingService:
    """Get scraping service instance."""
    return ScrapingService()

# ------------------------------ ERROR HANDLERS ------------------------------
def create_error_response(message: str, status_code: int = 500) -> dict:
    """Create standardized error response."""
    return {
        "success": False,
        "error": message,
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------------------ DATA ENDPOINTS ------------------------------
@router.get("/vehicles")
async def get_vehicles(account_id: int = 1):
    """Get cached vehicle data from database."""
    try:
        vehicles = get_vehicles_by_account(account_id)
        return {
            "success": True,
            "data": [vehicle.to_dict() for vehicle in vehicles],
            "count": len(vehicles),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve vehicle data")
        )

@router.get("/trips")
async def get_trips(account_id: int = 1, limit: int = 100):
    """Get cached trip data from database."""
    try:
        trips = get_trips_by_account(account_id, limit)
        return {
            "success": True,
            "data": [trip.to_dict() for trip in trips],
            "count": len(trips),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting trips: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve trip data")
        )

@router.get("/reviews")
async def get_reviews(account_id: int = 1, limit: int = 100):
    """Get cached review data from database."""
    try:
        reviews = get_reviews_by_account(account_id, limit)
        return {
            "success": True,
            "data": [review.to_dict() for review in reviews],
            "count": len(reviews),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting reviews: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve review data")
        )

@router.get("/earnings")
async def get_earnings(account_id: int = 1):
    """Get cached earnings data from database."""
    try:
        # Note: You'll need to implement get_earnings_by_account in your database operations
        return {
            "success": True,
            "message": "Earnings endpoint - implement get_earnings_by_account in database operations",
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting earnings: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve earnings data")
        )

# ------------------------------ SCRAPING ENDPOINTS ------------------------------
@router.post("/scrape/vehicles")
async def scrape_vehicles(
    account_id: int = 1,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """Trigger vehicle scraping in background."""
    try:
        task_id = await scraping_service.scrape_vehicles(account_id)
        return {
            "success": True,
            "message": "Vehicle scraping started",
            "task_id": task_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting vehicle scraping: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to start vehicle scraping")
        )

@router.post("/scrape/trips")
async def scrape_trips(
    account_id: int = 1,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """Trigger trip scraping in background."""
    try:
        task_id = await scraping_service.scrape_trips(account_id)
        return {
            "success": True,
            "message": "Trip scraping started",
            "task_id": task_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting trip scraping: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to start trip scraping")
        )

@router.post("/scrape/earnings")
async def scrape_earnings(
    account_id: int = 1,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """Trigger earnings scraping in background."""
    try:
        task_id = await scraping_service.scrape_earnings(account_id)
        return {
            "success": True,
            "message": "Earnings scraping started",
            "task_id": task_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting earnings scraping: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to start earnings scraping")
        )

@router.post("/scrape/reviews")
async def scrape_reviews(
    account_id: int = 1,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """Trigger review scraping in background."""
    try:
        task_id = await scraping_service.scrape_reviews(account_id)
        return {
            "success": True,
            "message": "Review scraping started",
            "task_id": task_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting review scraping: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to start review scraping")
        )

@router.post("/scrape/all")
async def scrape_all(
    account_id: int = 1,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """Trigger all data scraping in background."""
    try:
        task_id = await scraping_service.scrape_all(account_id)
        return {
            "success": True,
            "message": "All data scraping started",
            "task_id": task_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting all scraping: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to start comprehensive scraping")
        )

# ------------------------------ TASK MANAGEMENT ENDPOINTS ------------------------------
@router.get("/tasks")
async def get_all_tasks(scraping_service: ScrapingService = Depends(get_scraping_service)):
    """Get status of all active scraping tasks."""
    try:
        tasks = scraping_service.get_all_tasks()
        task_counts = scraping_service.get_task_count()
        return {
            "success": True,
            "data": tasks,
            "total_tasks": len(tasks),
            "task_counts": task_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve task information")
        )

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, scraping_service: ScrapingService = Depends(get_scraping_service)):
    """Get status of a specific scraping task."""
    try:
        task = scraping_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "success": True,
            "data": task,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve task status")
        )

@router.delete("/tasks/completed")
async def clear_completed_tasks(scraping_service: ScrapingService = Depends(get_scraping_service)):
    """Clear completed and failed tasks from memory."""
    try:
        scraping_service.clear_completed_tasks()
        return {
            "success": True,
            "message": "Completed tasks cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing tasks: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to clear completed tasks")
        )

# ------------------------------ STATISTICS ENDPOINTS ------------------------------
@router.get("/stats")
async def get_stats(account_id: int = 1):
    """Get database statistics for an account."""
    try:
        stats = get_database_stats(account_id)
        return {
            "success": True,
            "data": stats,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500, 
            detail=create_error_response("Failed to retrieve statistics")
        )
