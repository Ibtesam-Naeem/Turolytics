# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging

from .service import turo_service

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter(prefix="/turo", tags=["turo"])

# ------------------------------ SCRAPING ENDPOINTS ------------------------------

@router.post("/scrape")
async def start_scraping(
    email: str,
    data_types: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """Start scraping data for a Turo account.
    
    Args:
        email: Turo account email address.
        data_types: List of data types to scrape (vehicles, trips, earnings, reviews).
                   If None, scrapes all types.
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        Dictionary containing task IDs and account information.
    """
    try:
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        valid_types = {"vehicles", "trips", "earnings", "reviews"}
        if data_types:
            invalid_types = set(data_types) - valid_types
            if invalid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid data types: {list(invalid_types)}. Valid types: {list(valid_types)}"
                )
        
        results = await turo_service.scrape_account_data(email, data_types)
        
        logger.info(f"Started scraping for {email}: {results}")
        return {
            "success": True,
            "message": "Scraping started successfully",
            "data": results
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error starting scraping for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a scraping task.
    
    Args:
        task_id: Task ID to check.
        
    Returns:
        Dictionary containing task status information.
    """
    try:
        task_status = turo_service.get_task_status(task_id)
        
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

@router.get("/tasks")
async def get_all_tasks() -> Dict[str, Any]:
    """Get all active scraping tasks.
    
    Returns:
        Dictionary containing all tasks and their statuses.
    """
    try:
        tasks = turo_service.get_all_tasks()
        
        return {
            "success": True,
            "data": {
                "tasks": tasks,
                "total_tasks": len(tasks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@router.delete("/tasks/cleanup")
async def cleanup_tasks(keep_recent: int = 10) -> Dict[str, Any]:
    """Clean up completed and failed tasks.
    
    Args:
        keep_recent: Number of recent completed/failed tasks to keep.
        
    Returns:
        Dictionary containing cleanup results.
    """
    try:
        if keep_recent < 0:
            raise HTTPException(status_code=400, detail="keep_recent must be non-negative")
        
        results = turo_service.clear_completed_tasks(keep_recent)
        
        return {
            "success": True,
            "message": "Tasks cleaned up successfully",
            "data": results
        }
        
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup tasks: {str(e)}")

# ------------------------------ ACCOUNT ENDPOINTS ------------------------------

@router.get("/accounts/{account_id}/stats")
async def get_account_stats(account_id: int) -> Dict[str, Any]:
    """Get statistics for a specific account.
    
    Args:
        account_id: Account ID to get stats for.
        
    Returns:
        Dictionary containing account statistics.
    """
    try:
        if account_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid account ID")
        
        stats = turo_service.get_account_stats(account_id)
        
        return {
            "success": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for account {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account stats: {str(e)}")

# ------------------------------ HEALTH CHECK ------------------------------

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Turo service.
    
    Returns:
        Dictionary containing service health status.
    """
    try:
        task_count = turo_service.scraping_service.get_task_count()
        
        return {
            "success": True,
            "service": "turo",
            "status": "healthy",
            "data": {
                "task_counts": task_count,
                "total_tasks": sum(task_count.values())
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "service": "turo",
            "status": "unhealthy",
            "error": str(e)
        }

# ------------------------------ END OF FILE ------------------------------