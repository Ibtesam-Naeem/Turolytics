# ------------------------------ IMPORTS ------------------------------
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import only what's needed
from database import (
    get_vehicles_by_account, 
    get_trips_by_account, 
    get_reviews_by_account,
    get_database_stats
)
from services.scraping_service import ScrapingService
from config import settings

# ------------------------------ LOGGING ------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

# ------------------------------ LIFECYCLE MANAGEMENT ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("🚀 Starting Turolytics API...")
    yield
    logger.info("🛑 Shutting down Turolytics API...")

# ------------------------------ FASTAPI APP ------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description="Turo fleet analytics and data scraping API - Portfolio Project",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# ------------------------------ HEALTH ENDPOINTS ------------------------------
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Turolytics API - Portfolio Project",
        "version": settings.APP_VERSION,
        "description": "Turo fleet analytics and data scraping API",
        "features": [
            "Automated Turo data scraping",
            "Real-time vehicle tracking", 
            "Financial analytics",
            "Customer review analysis"
        ],
        "integrations": {
            "enabled": settings.get_enabled_integrations()
        },
        "endpoints": {
            "health": "/health",
            "vehicles": "/api/vehicles",
            "trips": "/api/trips", 
            "earnings": "/api/earnings",
            "reviews": "/api/reviews",
            "scrape": "/api/scrape/*"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        from database import get_db
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        database_status = "connected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        database_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "Turolytics API",
        "database": database_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------------------ DATA ENDPOINTS ------------------------------
@app.get("/api/vehicles")
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

@app.get("/api/trips")
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

@app.get("/api/reviews")
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

@app.get("/api/earnings")
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
@app.post("/api/scrape/vehicles")
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

@app.post("/api/scrape/trips")
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

@app.post("/api/scrape/earnings")
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

@app.post("/api/scrape/reviews")
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

@app.post("/api/scrape/all")
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
@app.get("/api/tasks")
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

@app.get("/api/tasks/{task_id}")
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

@app.delete("/api/tasks/completed")
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
@app.get("/api/stats")
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

# ------------------------------ MAIN EXECUTION ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )