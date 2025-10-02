# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from core.utils.logger import logger
from .auth import auth_manager, get_bouncie_auth_headers, is_bouncie_authenticated
from .service import bouncie_service

# ------------------------------ ROUTER SETUP ------------------------------

router = APIRouter(prefix="/bouncie", tags=["Bouncie"])

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.get("/auth/url")
async def get_auth_url():
    """Get Bouncie OAuth 2.0 authorization URL."""
    try:
        auth_url = auth_manager.get_authorization_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "Visit this URL to authorize the application"
        }
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    """Handle OAuth 2.0 callback and exchange code for token."""
    try:
        logger.info(f"Processing OAuth callback with code: {code[:20]}...")
        
        # Exchange code for token
        token = await auth_manager.exchange_code_for_token(code)
        
        # Start auto refresh
        await auth_manager.start_auto_refresh()
        
        return {
            "success": True,
            "message": "Successfully authenticated with Bouncie",
            "user_id": token.user_id,
            "expires_at": token.expires_at.isoformat(),
            "expires_in_seconds": token.expires_in_seconds
        }
        
    except Exception as e:
        logger.error(f"Error processing auth callback: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/auth/status")
async def get_auth_status():
    """Get current authentication status."""
    try:
        is_authenticated = is_bouncie_authenticated()
        token_info = auth_manager.get_token_info()
        
        return {
            "success": True,
            "is_authenticated": is_authenticated,
            "token_info": token_info
        }
        
    except Exception as e:
        logger.error(f"Error getting auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/refresh")
async def refresh_token():
    """Manually refresh the access token."""
    try:
        token = await auth_manager.refresh_token()
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "expires_at": token.expires_at.isoformat(),
            "expires_in_seconds": token.expires_in_seconds
        }
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ------------------------------ DATA ROUTES ------------------------------

@router.get("/user")
async def get_user():
    """Get user information."""
    try:
        result = await bouncie_service.get_user_info()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles")
async def get_vehicles():
    """Get vehicles information."""
    try:
        result = await bouncie_service.get_vehicles()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations")
async def get_locations():
    """Get locations information."""
    try:
        result = await bouncie_service.get_locations()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trips")
async def get_trips(
    gps_format: str = Query("geojson", description="GPS format: geojson or polyline"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get trips information."""
    try:
        result = await bouncie_service.get_trips(gps_format, start_date, end_date)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trips: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/{vehicle_id}/trips")
async def get_vehicle_trips(
    vehicle_id: str,
    gps_format: str = Query("geojson", description="GPS format: geojson or polyline"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get trips for a specific vehicle."""
    try:
        result = await bouncie_service.get_vehicle_trips(vehicle_id, gps_format, start_date, end_date)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trips for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/{vehicle_id}/location")
async def get_vehicle_location(vehicle_id: str):
    """Get current location of a specific vehicle."""
    try:
        result = await bouncie_service.get_vehicle_location(vehicle_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles/{vehicle_id}/diagnostics")
async def get_vehicle_diagnostics(vehicle_id: str):
    """Get diagnostics for a specific vehicle."""
    try:
        result = await bouncie_service.get_vehicle_diagnostics(vehicle_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=result.get("status_code", 500), detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagnostics for vehicle {vehicle_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------ SYNC ROUTES ------------------------------

@router.post("/sync")
async def sync_data():
    """Sync all available Bouncie data."""
    try:
        logger.info("Starting Bouncie data sync...")
        result = await bouncie_service.sync_all_data()
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Data sync completed: {result['successful_count']}/{result['total_count']} operations successful",
                "results": result["results"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during data sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------ HEALTH ROUTES ------------------------------

@router.get("/health")
async def health_check():
    """Health check for Bouncie service."""
    try:
        is_authenticated = is_bouncie_authenticated()
        token_info = auth_manager.get_token_info()
        
        return {
            "success": True,
            "status": "healthy",
            "is_authenticated": is_authenticated,
            "token_info": token_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ------------------------------ END OF FILE ------------------------------
