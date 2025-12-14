# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Query, Depends, HTTPException, Path
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from .scraping_service import ScrapingService
from core.database.models.account import Account
from core.database.models.turo_integration import TuroIntegration
from core.database import get_db
from core.security.auth import get_current_active_user
from core.security.encryption import encrypt_password, decrypt_password
from .data.login import start_turo_login, submit_turo_2fa_code
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
    email: Optional[str] = None  # Optional if credentials are stored
    password: Optional[str] = None  # Optional if credentials are stored

class TuroConnectRequest(BaseModel):
    email: str
    password: str

class Turo2FARequest(BaseModel):
    session_id: str
    code: str

class ScrapeResponse(BaseModel):
    task_id: str
    account_id: int
    scraper_type: str

# ------------------------------ AUTHENTICATION ENDPOINTS ------------------------------

@router.get("/auth/status", response_model=APIResponse, tags=["Authentication"])
async def get_turo_integration_status(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if account has Turo credentials stored.
    Returns integration status for authenticated user.
    """
    try:
        integration = db.query(TuroIntegration).filter(
            TuroIntegration.account_id == current_user.id
        ).first()
        
        if not integration:
            return APIResponse(
                success=True,
                data={
                    "connected": False,
                    "message": "No Turo integration found for this account"
                }
            )
        
        return APIResponse(
            success=True,
            data={
                "connected": True,
                "email": integration.turo_email,
                "has_active_session": integration.has_active_session == "True",
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() if integration.updated_at else None
            }
        )
    
    except Exception as e:
        logger.exception(f"Error checking Turo integration status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/auth/connect", response_model=APIResponse, tags=["Authentication"])
async def connect_turo(
    request: TuroConnectRequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start Turo login process and store credentials.
    If 2FA is required, returns session_id for 2FA submission.
    """
    try:
        # Store credentials first (encrypted)
        encrypted_password = encrypt_password(request.password)
        
        integration = db.query(TuroIntegration).filter(
            TuroIntegration.account_id == current_user.id
        ).first()
        
        if integration:
            integration.turo_email = request.email
            integration.turo_password_encrypted = encrypted_password
            integration.has_active_session = "False"  # Will be set to True after successful login
        else:
            integration = TuroIntegration(
                account_id=current_user.id,
                turo_email=request.email,
                turo_password_encrypted=encrypted_password,
                has_active_session="False"
            )
            db.add(integration)
        
        db.commit()
        logger.info(f"Turo credentials stored for account {current_user.id}")
        
        # Start login process
        login_result = await start_turo_login(
            account_id=current_user.user_id,
            email=request.email,
            password=request.password
        )
        
        if not login_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=login_result.get("error", "Login failed")
            )
        
        # If 2FA is required, return session_id
        if login_result.get("requires_2fa"):
            return APIResponse(
                success=True,
                data={
                    "requires_2fa": True,
                    "session_id": login_result.get("session_id"),
                    "message": "2FA code required. Please submit the code using /auth/connect/2fa"
                }
            )
        
        # Login successful without 2FA - update session status
        integration.has_active_session = "True"
        db.commit()
        
        # Check if this is first-time connection (no existing trips/vehicles)
        # If so, automatically trigger full data scrape
        from .service import TuroDataService
        data_service = TuroDataService(db)
        existing_trips, _ = data_service.get_trips(current_user, limit=1)
        is_first_connection = len(existing_trips) == 0
        
        # Auto-scrape on first connection
        task_id = None
        if is_first_connection:
            try:
                task_id = await SCRAPER_MAP["all"](current_user.user_id, request.email, request.password)
                logger.info(f"Auto-started full data scrape for new Turo connection: {task_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-start scrape after connection: {e}")
                # Don't fail the connection if scraping fails
        
        return APIResponse(
            success=True,
            data={
                "message": "Turo account connected successfully",
                "email": integration.turo_email,
                "account_id": current_user.id,
                "requires_2fa": False,
                "auto_scrape_task_id": task_id  # Include task_id if scraping started
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error connecting Turo: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/auth/connect/2fa", response_model=APIResponse, tags=["Authentication"])
async def submit_turo_2fa(
    request: Turo2FARequest,
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit 2FA code to complete Turo login.
    """
    try:
        result = await submit_turo_2fa_code(request.session_id, request.code)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "2FA submission failed")
            )
        
        # Get email and account_id from result (session is cleaned up in submit_turo_2fa_code)
        email = result.get("email")
        account_id = result.get("account_id")
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve email from login session"
            )
        
        # Update integration to mark session as active
        integration = db.query(TuroIntegration).filter(
            TuroIntegration.account_id == current_user.id
        ).first()
        
        if integration:
            # Update existing - session is now active
            integration.has_active_session = "True"
        else:
            # This shouldn't happen, but handle gracefully
            logger.warning(f"Integration not found for account {current_user.id} after 2FA success")
        
        # Check if this is first-time connection (no existing trips/vehicles)
        # If so, automatically trigger full data scrape
        from .service import TuroDataService
        data_service = TuroDataService(db)
        existing_trips, _ = data_service.get_trips(current_user, limit=1)
        is_first_connection = len(existing_trips) == 0
        
        db.commit()
        
        # Auto-scrape on first connection
        task_id = None
        if is_first_connection and integration:
            try:
                # Get password from stored integration
                password = decrypt_password(integration.turo_password_encrypted)
                task_id = await SCRAPER_MAP["all"](current_user.user_id, email, password)
                logger.info(f"Auto-started full data scrape for new Turo connection: {task_id}")
            except Exception as e:
                logger.warning(f"Failed to auto-start scrape after 2FA: {e}")
                # Don't fail the connection if scraping fails
        
        return APIResponse(
            success=True,
            data={
                "message": "Turo account connected successfully",
                "email": email,
                "account_id": current_user.id,
                "auto_scrape_task_id": task_id  # Include task_id if scraping started
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error submitting 2FA: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/auth/disconnect", response_model=APIResponse, tags=["Authentication"])
async def disconnect_turo(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove Turo credentials for authenticated user.
    """
    try:
        integration = db.query(TuroIntegration).filter(
            TuroIntegration.account_id == current_user.id
        ).first()
        
        if not integration:
            raise HTTPException(
                status_code=404,
                detail="No Turo integration found for this account"
            )
        
        db.delete(integration)
        db.commit()
        
        logger.info(f"Turo integration removed for account {current_user.id}")
        
        return APIResponse(
            success=True,
            data={
                "message": "Turo integration disconnected successfully",
                "account_id": current_user.id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error disconnecting Turo: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
    scraper_type: str = Path(..., pattern="^(all|vehicles|trips|reviews|earnings)$", description="Type of data to scrape"),
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ScrapeResponse:
    """Scrape data of specified type on demand. Uses authenticated user's account."""
    try:
        # Get credentials from request or stored integration
        email = request.email
        password = request.password
        
        if not email or not password:
            # Try to get from stored integration
            integration = db.query(TuroIntegration).filter(
                TuroIntegration.account_id == current_user.id
            ).first()
            
            if integration:
                email = integration.turo_email
                password = decrypt_password(integration.turo_password_encrypted)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Turo credentials required. Either provide email/password in request or connect Turo account first."
                )
        
        task_id = await SCRAPER_MAP[scraper_type](current_user.user_id, email, password)
        logger.info(f"Started {scraper_type} scraping for {current_user.email}: {task_id}")
        return ScrapeResponse(task_id=task_id, account_id=current_user.user_id, scraper_type=scraper_type)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid scraper type: {scraper_type}")
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Scraping runtime error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
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
    trip_id: Optional[str] = Query(None, description="Filter by specific trip ID"),
    status: Optional[str] = Query(None, description="Filter by trip status (COMPLETED, CANCELLED, etc.)"),
    trip_type: Optional[str] = Query(None, description="Filter by trip type (booked_trips, trip_history)"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Filter trips created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter trips created on or before this date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get trips with filtering and pagination."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400, 
            detail="start_date must be before or equal to end_date"
        )
    
    trips, total = service.get_trips(
        account=current_user,
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
        data={
            "trips": [TripOut.model_validate(t, from_attributes=True) for t in trips],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/data/vehicles", response_model=APIResponse, response_model_exclude_none=True, tags=["Vehicles"])
async def get_vehicles(
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    license_plate: Optional[str] = Query(None, description="Filter by license plate"),
    status: Optional[str] = Query(None, description="Filter by status (Listed, Snoozed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get vehicles with filtering and pagination."""
    vehicles, total = service.get_vehicles(
        account=current_user,
        vehicle_id=vehicle_id,
        license_plate=license_plate,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return APIResponse(
        success=True,
        data={
            "vehicles": [VehicleOut.model_validate(v, from_attributes=True) for v in vehicles],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/data/reviews", response_model=APIResponse, response_model_exclude_none=True, tags=["Reviews"])
async def get_reviews(
    review_id: Optional[int] = Query(None, description="Filter by review ID"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0, description="Minimum rating"),
    has_response: Optional[bool] = Query(None, description="Filter by host response"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Account = Depends(get_current_active_user),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get reviews with filtering and pagination."""
    reviews, total = service.get_reviews(
        account=current_user,
        review_id=review_id,
        vehicle_id=vehicle_id,
        min_rating=min_rating,
        has_response=has_response,
        limit=limit,
        offset=offset
    )
    
    return APIResponse(
        success=True,
        data={
            "reviews": [ReviewOut.model_validate(r, from_attributes=True) for r in reviews],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.get("/data/earnings", response_model=APIResponse, response_model_exclude_none=True, tags=["Earnings"])
async def get_earnings(
    year: Optional[int] = Query(None, description="Filter by year"),
    current_user: Account = Depends(get_current_active_user),
    service: TuroDataService = Depends(get_turo_data_service)
) -> APIResponse:
    """Get earnings data."""
    breakdowns, vehicle_earnings = service.get_earnings(account=current_user, year=year)
    
    return APIResponse(
        success=True,
        data={
            "breakdown": [EarningsBreakdownOut.model_validate(b, from_attributes=True) for b in breakdowns],
            "vehicle_earnings": [VehicleEarningsOut.model_validate(v, from_attributes=True) for v in vehicle_earnings],
            "total_breakdown_items": len(breakdowns),
            "total_vehicles": len(vehicle_earnings)
        }
    )

# ------------------------------ END OF FILE ------------------------------
