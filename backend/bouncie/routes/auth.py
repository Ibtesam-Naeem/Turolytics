# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
import asyncio
from datetime import datetime, timezone

from ..service import BouncieService
from ..schemas import APIResponse
from ..constants import DEFAULT_TOKEN_EXPIRY_SECONDS
from core.database import get_db
from core.database.models import (
    Account, BouncieTripMatch, BouncieVehicleMapping, 
    BouncieDTCCode, BouncieWebhookLog
)
from core.security.auth import get_current_active_user
from core.utils.route_helpers import get_bouncie_integration, handle_route_errors
from sqlalchemy.orm import Session
from .dependencies import get_bouncie_service

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ AUTHENTICATION ROUTES ------------------------------

@router.get("/auth/url", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("getting authorization URL")
async def get_authorization_url(
    popup: bool = Query(False, description="Whether this is for a popup window (adds popup param to callback)"),
    service: BouncieService = Depends(get_bouncie_service)
):
    """Get Bouncie OAuth authorization URL."""
    state = str(service.account.user_id)
    url = service.get_authorization_url(state)
    if popup:
        url += f"&popup=true"
    return APIResponse(success=True, data={"authorization_url": url})

@router.get("/auth/status", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("checking integration status")
async def get_integration_status(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if account has an active Bouncie integration."""
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        return APIResponse(
            success=True,
            data={
                "connected": False,
                "message": "No Bouncie integration found for this account"
            }
        )
    
    is_expired = integration.expires_at < datetime.now(timezone.utc) if integration.expires_at else True
    
    return APIResponse(
        success=True,
        data={
            "connected": True,
            "expired": is_expired,
            "bouncie_user_id": integration.bouncie_user_id,
            "bouncie_user_email": integration.bouncie_user_email,
            "expires_at": integration.expires_at.isoformat() if integration.expires_at else None,
            "created_at": integration.created_at.isoformat() if integration.created_at else None,
            "updated_at": integration.updated_at.isoformat() if integration.updated_at else None
        }
    )

@router.delete("/auth/disconnect", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("disconnecting integration", rollback_db=True)
async def disconnect_integration(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect Bouncie integration for authenticated user."""
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="No Bouncie integration found for this account"
        )

    db.delete(integration)
    db.commit()
    
    logger.info(f"Disconnected Bouncie integration for account {current_user.id}")
    
    return APIResponse(
        success=True,
        data={
            "message": "Bouncie integration disconnected successfully",
            "account_id": current_user.id
        }
    )

@router.delete("/auth/delete-all-data", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("deleting all Bouncie data", rollback_db=True)
async def delete_all_bouncie_data(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete ALL Bouncie-related data for authenticated user."""
    deletion_summary = {
        "trip_matches_deleted": 0,
        "vehicle_mappings_deleted": 0,
        "dtc_codes_deleted": 0,
        "webhook_logs_deleted": 0,
        "integration_deleted": False
    }
    
    trip_matches = db.query(BouncieTripMatch).filter(
        BouncieTripMatch.account_id == current_user.id
    ).all()
    deletion_summary["trip_matches_deleted"] = len(trip_matches)
    for match in trip_matches:
        db.delete(match)
    
    vehicle_mappings = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == current_user.id
    ).all()
    deletion_summary["vehicle_mappings_deleted"] = len(vehicle_mappings)
    for mapping in vehicle_mappings:
        db.delete(mapping)
    
    dtc_codes = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == current_user.id
    ).all()
    deletion_summary["dtc_codes_deleted"] = len(dtc_codes)
    for code in dtc_codes:
        db.delete(code)
    
    webhook_logs = db.query(BouncieWebhookLog).filter(
        BouncieWebhookLog.account_id == current_user.id
    ).all()
    deletion_summary["webhook_logs_deleted"] = len(webhook_logs)
    for log in webhook_logs:
        db.delete(log)
    
    integration = get_bouncie_integration(db, current_user.id)
    if integration:
        db.delete(integration)
        deletion_summary["integration_deleted"] = True
    
    db.commit()
    
    logger.info(
        f"Deleted all Bouncie data for account {current_user.id}: "
        f"{deletion_summary['trip_matches_deleted']} trip matches, "
        f"{deletion_summary['vehicle_mappings_deleted']} vehicle mappings, "
        f"{deletion_summary['dtc_codes_deleted']} DTC codes, "
        f"{deletion_summary['webhook_logs_deleted']} webhook logs, "
        f"integration: {deletion_summary['integration_deleted']}"
    )
    
    return APIResponse(
        success=True,
        data={
            "message": "All Bouncie data deleted successfully",
            "account_id": current_user.id,
            "deletion_summary": deletion_summary
        }
    )

@router.get("/auth/token", response_model=APIResponse, tags=["Authentication"])
@handle_route_errors("getting access token")
async def get_access_token(
    current_user: Account = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get access token for frontend to use directly with Bouncie API."""
    logger.debug(f"Token request from user {current_user.id}")
    integration = get_bouncie_integration(db, current_user.id)
    
    if not integration:
        logger.warning(f"No Bouncie integration found for user {current_user.id}")
        raise HTTPException(
            status_code=404,
            detail="Bouncie not connected for this account"
        )
    
    service = BouncieService(db=db, account=current_user)
    
    if integration.expires_at and integration.expires_at < datetime.now(timezone.utc):
        logger.info(f"Token expired for account {current_user.id}, refreshing")
        refresh_success = await asyncio.to_thread(service._refresh_access_token)
        if not refresh_success:
            logger.error(f"Token refresh failed for account {current_user.id}")
            raise HTTPException(
                status_code=401,
                detail="Token expired and refresh failed. Please reconnect Bouncie."
            )
    
    service._load_tokens()
    
    if not service.access_token:
        logger.error(f"No access token available for account {current_user.id}")
        raise HTTPException(
            status_code=401,
            detail="No access token available. Please reconnect Bouncie."
        )
    
    expires_in = DEFAULT_TOKEN_EXPIRY_SECONDS
    if integration.expires_at:
        expires_in = int((integration.expires_at - datetime.now(timezone.utc)).total_seconds())
        expires_in = max(0, expires_in)
    
    logger.debug(f"Token provided to user {current_user.id}, expires in {expires_in}s")
    return APIResponse(
        success=True,
        data={
            "access_token": service.access_token,
            "expires_in": expires_in,
            "token_type": "Bearer"
        }
    )

# ------------------------------ END OF FILE ------------------------------