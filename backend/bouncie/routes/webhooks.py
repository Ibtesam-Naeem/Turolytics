# ------------------------------ IMPORTS ------------------------------
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import json
import os
import hmac
import hashlib
import asyncio
from datetime import datetime, timezone

from ..service import BouncieService
from ..helpers import normalize_imei
from ..trip_processor import process_bouncie_link
from ..constants import WEBHOOK_TRIP_MATCH_DAYS_BACK
from ..schemas import APIResponse
from core.database import get_db
from core.database.connection import SessionLocal
from core.database.models import (
    BouncieVehicleMapping, BouncieWebhookLog, BouncieDTCCode
)
from core.utils.route_helpers import handle_route_errors
from sqlalchemy.orm import Session
from .dependencies import get_bouncie_service

logger = logging.getLogger(__name__)

# ------------------------------ ROUTER SETUP ------------------------------
router = APIRouter()

# ------------------------------ WEBHOOK ROUTES ------------------------------

@router.get("/webhooks/events", response_model=APIResponse, tags=["Webhooks"])
@handle_route_errors("getting webhook events")
async def get_webhook_events(service: BouncieService = Depends(get_bouncie_service)):
    """Get available webhook events."""
    events = service.get_webhook_events()
    return APIResponse(success=True, data={"events": events})

@router.get("/webhooks/url", response_model=APIResponse, tags=["Webhooks"])
@handle_route_errors("getting webhook URL")
async def get_webhook_url():
    """Get the webhook URL that should be registered with Bouncie."""
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    webhook_url = f"{backend_url}/api/bouncie/webhooks/bouncie"
    
    return APIResponse(
        success=True,
        data={
            "webhook_url": webhook_url,
            "instructions": "Register this URL in your Bouncie developer dashboard to receive webhook events. Make sure your backend is publicly accessible (HTTPS required for production)."
        }
    )

def _verify_webhook_signature(body_bytes: bytes, signature: str, secret: str) -> bool:
    """
    Verify Bouncie webhook signature.
    Bouncie uses HMAC-SHA256 to sign webhooks.
    
    Args:
        body_bytes: Raw request body as bytes
        signature: Signature from X-Bouncie-Signature header
        secret: Webhook secret from Bouncie
    
    Returns:
        True if signature is valid, False otherwise
    """
    if signature is None or secret is None:
        return False
    
    try:
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

def _get_data(payload: dict) -> dict:
    """Safely extract data from payload."""
    d = payload.get("data")
    return d if isinstance(d, dict) else {}

def _sanitize_headers(headers: dict) -> dict:
    """Extract only whitelisted safe headers."""
    safe_header_names = {
        'x-bouncie-signature', 'x-signature', 'content-type', 
        'user-agent', 'x-forwarded-for', 'x-forwarded-proto',
        'host', 'content-length'
    }
    
    return {
        key: value 
        for key, value in headers.items() 
        if key.lower() in safe_header_names
    }

@router.post("/webhooks/bouncie", tags=["Webhooks"])
@handle_route_errors("processing Bouncie webhook", rollback_db=False)
async def handle_bouncie_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle incoming webhooks from Bouncie."""
    body_bytes = await request.body()
    sanitized_headers = _sanitize_headers(dict(request.headers))
    payload_hash = hashlib.sha256(body_bytes).hexdigest()
    
    webhook_log = BouncieWebhookLog(
        event_type="unknown",
        raw_payload={},
        processed=False,
        signature_valid=None,
        headers=sanitized_headers
    )
    db.add(webhook_log)
    
    try:
        payload = json.loads(body_bytes.decode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        webhook_log.error_message = f"Invalid JSON payload: {str(e)}"
        webhook_log.raw_payload = {"_hash": payload_hash}
        db.commit()
        return JSONResponse({"status": "error", "message": "Invalid JSON payload"}, status_code=400)
    
    webhook_secret = os.getenv("BOUNCIE_WEBHOOK_SECRET")
    signature = request.headers.get("X-Bouncie-Signature") or request.headers.get("X-Signature")
    signature_valid = None
    
    if webhook_secret and signature:
        signature_valid = _verify_webhook_signature(body_bytes, signature, webhook_secret)
        webhook_log.signature_valid = signature_valid
        if not signature_valid:
            logger.warning("Webhook signature verification failed - possible security issue")
            webhook_log.event_type = payload.get("event", "unknown")
            webhook_log.imei = payload.get("imei")
            webhook_log.raw_payload = payload
            webhook_log.error_message = "Invalid webhook signature"
            db.commit()
            return JSONResponse({"status": "error", "message": "Invalid signature"}, status_code=401)
    elif webhook_secret and not signature:
        logger.warning("Webhook secret configured but no signature provided")
        signature_valid = False
        webhook_log.signature_valid = False
    else:
        logger.info("Webhook signature verification skipped (no secret configured)")
        signature_valid = None
        webhook_log.signature_valid = None
    
    event_type = payload.get("event") or payload.get("type")
    if not event_type:
        logger.warning("Webhook received without event type")
        webhook_log.raw_payload = payload
        webhook_log.error_message = "Missing event type"
        db.commit()
        return JSONResponse({"status": "error", "message": "Missing event type"}, status_code=400)
    
    data = _get_data(payload)
    imei = payload.get("imei") or payload.get("device_imei") or data.get("imei")
    
    account_id = None
    vehicle_id = None
    if imei is not None:
        mapping = db.query(BouncieVehicleMapping).filter(
            BouncieVehicleMapping.imei == normalize_imei(imei)
        ).first()
        if mapping:
            account_id = mapping.account_id
            vehicle_id = mapping.vehicle_id
        else:
            logger.warning(f"No vehicle mapping found for IMEI {imei} - webhook logged but not processed")
    else:
        logger.warning("Webhook received without IMEI")
    
    webhook_log.account_id = account_id
    webhook_log.vehicle_id = vehicle_id
    webhook_log.event_type = event_type
    webhook_log.imei = imei
    
    should_store_full_payload = (
        signature_valid is False or
        event_type in ("new_mil_event", "vin_change")
    )
    
    if should_store_full_payload:
        webhook_log.raw_payload = payload
    else:
        webhook_log.raw_payload = {"_hash": payload_hash}
    
    db.flush()
    
    try:
        if event_type == "new_mil_event":
            if account_id is not None and vehicle_id is not None:
                await _handle_mil_event(db, account_id, vehicle_id, imei, payload)
        elif event_type == "trip_ended":
            if account_id is not None and vehicle_id is not None:
                background_tasks.add_task(
                    _handle_trip_ended_background,
                    account_id,
                    vehicle_id,
                    imei
                )
        elif event_type in ("device_connected", "device_disconnected"):
            if account_id is not None and vehicle_id is not None:
                logger.info(f"Device {event_type} for IMEI {imei}, account {account_id}")
        elif event_type == "vin_change":
            if account_id is not None and vehicle_id is not None:
                await _handle_vin_change(db, account_id, vehicle_id, imei, payload)
        elif event_type == "new_trip_data":
            logger.info(f"New trip data for device {imei}, account {account_id}")
        elif event_type == "new_battery_status":
            logger.info(f"Battery status update for device {imei}, account {account_id}")
        else:
            logger.info(f"Unhandled webhook event type: {event_type} for IMEI {imei}")
        
        webhook_log.processed = True
        db.commit()
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        webhook_log.processed = False
        webhook_log.error_message = str(e)
        if not should_store_full_payload:
            webhook_log.raw_payload = payload
        db.commit()
        return JSONResponse({"status": "error", "message": "Processing failed but logged"}, status_code=500)
    
    return {"status": "ok", "message": "Webhook processed"}

# ------------------------------ WEBHOOK HANDLERS ------------------------------

async def _handle_mil_event(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle new_mil_event webhook - store DTC codes."""
    logger.info(f"Processing MIL event for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    data = _get_data(payload)
    dtc_code = (
        data.get("code") or data.get("dtc") or data.get("dtc_code") or
        payload.get("code") or payload.get("dtc")
    )
    
    if not dtc_code:
        logger.warning(f"No DTC code found in MIL event payload")
        return
    
    description = (
        data.get("description") or data.get("message") or
        payload.get("description") or payload.get("message")
    )
    
    timestamp_str = (
        payload.get("timestamp") or payload.get("time") or
        data.get("timestamp") or data.get("time")
    )
    occurred_at = _parse_webhook_timestamp(timestamp_str)
    
    normalized_imei = normalize_imei(imei)
    existing_code = db.query(BouncieDTCCode).filter(
        BouncieDTCCode.account_id == account_id,
        BouncieDTCCode.imei == normalized_imei,
        BouncieDTCCode.code == dtc_code,
        BouncieDTCCode.is_active.is_(True)
    ).first()
    
    if existing_code:
        logger.info(f"DTC code {dtc_code} already exists and is active for IMEI {imei}")
        return
    
    dtc_record = BouncieDTCCode(
        account_id=account_id,
        vehicle_id=vehicle_id,
        imei=normalized_imei,
        code=dtc_code,
        description=description,
        is_active=True,
        occurred_at=occurred_at,
        raw_data=json.dumps(payload)
    )
    
    db.add(dtc_record)
    logger.info(f"Stored new DTC code: {dtc_code} ({description}) for IMEI {imei}, vehicle {vehicle_id}")
    return dtc_record

def _handle_trip_ended_background(
    account_id: int,
    vehicle_id: int,
    imei: str
):
    """Handle trip_ended webhook in background - trigger automatic trip matching."""
    logger.info(f"Processing trip_ended event in background for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(process_bouncie_link(
                db=db,
                account_id=account_id,
                days_back=WEBHOOK_TRIP_MATCH_DAYS_BACK,
                skip_existing_matches=False,
                force_rematch=False
            ))
            
            if result.get("success"):
                logger.info("Automatic trip matching triggered after trip_ended event")
            else:
                logger.warning(f"Trip matching failed after trip_ended: {result.get('error')}")
        finally:
            loop.close()
    except Exception as e:
        logger.exception(f"Error triggering trip matching after trip_ended: {e}")
    finally:
        db.close()

async def _handle_vin_change(
    db: Session,
    account_id: int,
    vehicle_id: int,
    imei: str,
    payload: dict
):
    """Handle vin_change webhook - update vehicle mapping with new VIN."""
    
    logger.info(f"Processing VIN change for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
    
    data = _get_data(payload)
    new_vin = (
        data.get("vin") or 
        data.get("new_vin") or
        payload.get("vin") or
        payload.get("new_vin")
    )
    
    if not new_vin:
        logger.warning(f"No VIN found in vin_change payload: {payload}")
        return
    
    normalized_imei = normalize_imei(imei)
    mapping = db.query(BouncieVehicleMapping).filter(
        BouncieVehicleMapping.account_id == account_id,
        BouncieVehicleMapping.vehicle_id == vehicle_id,
        BouncieVehicleMapping.imei == normalized_imei
    ).first()
    
    if not mapping:
        logger.warning(f"No mapping found for account {account_id}, vehicle {vehicle_id}, IMEI {imei}")
        return
    
    old_vin = mapping.bouncie_vin
    mapping.bouncie_vin = new_vin
    logger.info(f"Updated VIN for IMEI {imei}: {old_vin} -> {new_vin}")

def _parse_webhook_timestamp(timestamp_str: Optional[str]) -> datetime:
    """Parse webhook timestamp string to datetime."""
    if timestamp_str is None:
        return datetime.now(timezone.utc)
    
    try:
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        occurred_at = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        return occurred_at
    except Exception as e:
        logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
        return datetime.now(timezone.utc)

# ------------------------------ END OF FILE ------------------------------