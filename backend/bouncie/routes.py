from fastapi import APIRouter, HTTPException, Query, Header, Request
from typing import Dict, Any, Optional
import os
import hmac
import hashlib
import json

from .service import BouncieService, get_bouncie_vehicle_data

router = APIRouter(prefix="/bouncie", tags=["bouncie"])

@router.get("/auth/url")
async def get_auth_url():
    """Get Bouncie OAuth authorization URL."""
    service = BouncieService()
    auth_url = service.get_authorization_url()
    return {
        "auth_url": auth_url,
        "message": "Visit this URL to authorize Bouncie access"
    }

@router.post("/auth/callback")
async def handle_auth_callback(code: str):
    """Handle OAuth callback and get vehicle data."""
    try:
        result = await get_bouncie_vehicle_data(code)
        if result["success"]:
            return {
                "success": True,
                "message": "Successfully authenticated with Bouncie",
                "data": result
            }
        else:
            
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vehicles")
async def get_vehicles(auth_code: str = Query(..., description="Bouncie authorization code")):
    """Get vehicle data using authorization code."""
    try:
        result = await get_bouncie_vehicle_data(auth_code)
        if result["success"]:
            return {
                "success": True,
                "vehicles": result["vehicles"],
                "user": result["user"]["data"] if result["user"]["success"] else None
            }
        else:
            
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook/events")
async def get_webhook_events():
    """Get available webhook events."""
    service = BouncieService()
    return {
        "webhook_events": service.get_webhook_events(),
        "description": "Available Bouncie webhook events for real-time notifications"
    }

@router.post("/webhook/test")
async def test_webhook_payload(payload: Dict[str, Any]):
    """Test webhook payload validation."""
    service = BouncieService()
    is_valid = service.validate_webhook_payload(payload)
    
    return {
        "valid": is_valid,
        "payload": payload,
        "message": "Webhook payload validation result"
    }

# ------------------------------ WEBHOOK RECEIVER ------------------------------

@router.post("/webhook/receive")
async def receive_webhook(
    request: Request,
    x_bouncie_signature: Optional[str] = Header(None, alias="X-Bouncie-Signature"),
    x_signature: Optional[str] = Header(None, alias="X-Signature")
) -> Dict[str, Any]:
    """Receive real-time webhooks from Bouncie.
    
    Security:
        - If BOUNCIE_WEBHOOK_SECRET is set, verify HMAC-SHA256 signature against the raw body.
        - Accepts signature from 'X-Bouncie-Signature' or fallback 'X-Signature'.
    """
    try:
        raw_body: bytes = await request.body()
        try:
            payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        webhook_secret = os.getenv("BOUNCIE_WEBHOOK_SECRET", "").strip()
        provided_sig = x_bouncie_signature or x_signature or request.headers.get("X-Bouncie-Signature") or request.headers.get("X-Signature")
       
        if webhook_secret:
            if not provided_sig:
                raise HTTPException(status_code=401, detail="Missing webhook signature")
            expected_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(provided_sig, expected_sig):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        service = BouncieService()
        if not service.validate_webhook_payload(payload):
            raise HTTPException(status_code=400, detail="Invalid webhook payload structure")

        event_type = payload.get("event", "unknown")
        event_data = payload.get("data", {})

        return {
            "success": True,
            "message": f"Webhook received: {event_type}",
            "event": event_type,
            "timestamp": payload.get("timestamp"),
            "verified": bool(webhook_secret),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
