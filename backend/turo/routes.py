# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from core.services.scraping_service import ScrapingService
from core.utils.api_helpers import validate_credentials, get_account_id

logger = logging.getLogger(__name__)

# ------------------------------ HELPER FUNCTIONS ------------------------------

def get_account_id_from_params(account_id: Optional[int], email: Optional[str]) -> int:
    """Get account ID from either account_id or email parameter."""
    if not account_id and not email:
        raise HTTPException(status_code=400, detail="Either account_id or email is required")
    
    if not account_id and email:
        return get_account_id(email)
    
    return account_id

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
        return {"success": True, "data": task_status}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

# ------------------------------ END OF FILE ------------------------------