#!/usr/bin/env python3
"""
Bouncie API Routes
FastAPI routes for Bouncie vehicle data integration.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import asyncio

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
